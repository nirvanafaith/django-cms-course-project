"""公开内容浏览与组合查询合同测试。"""

from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase, override_settings
from django.urls import reverse

from content.models import Category, Item

SHANGHAI = ZoneInfo("Asia/Shanghai")


@override_settings(PUBLIC_PAGE_CACHE_ENABLED=False)
class PublicContentTests(TestCase):
    """验证匿名公开内容的筛选语义、草稿边界与稳定排序。"""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.news = Category.objects.create(name="交大头条", description="学校重点新闻")
        cls.notice = Category.objects.create(name="通知公告", description="服务通知")
        cls.draft = Item.objects.create(
            title="内部草稿不应公开",
            content="draft",
            category=cls.news,
            publish_time=datetime(2026, 8, 14, 9, tzinfo=SHANGHAI),
            is_published=False,
        )
        cls.early = Item.objects.create(
            title="交通强国早间新闻",
            content="early",
            category=cls.news,
            publish_time=datetime(2026, 8, 13, 9, tzinfo=SHANGHAI),
            is_published=True,
        )
        cls.equal_first = Item.objects.create(
            title="同一时刻第一篇",
            content="first",
            category=cls.notice,
            publish_time=datetime(2026, 8, 12, 9, tzinfo=SHANGHAI),
            is_published=True,
        )
        cls.equal_second = Item.objects.create(
            title="同一时刻第二篇",
            content="second",
            category=cls.notice,
            publish_time=cls.equal_first.publish_time,
            is_published=True,
        )

    def test_search_invalid_category_renders_recovery_state(self) -> None:
        """非法栏目值显示空结果和恢复入口，而不是回退为全部文章。"""
        response = self.client.get(reverse("content:search"), {"category": "不存在的栏目"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "选择一个有效的选项")
        self.assertContains(response, "没有找到相关文章")
        self.assertNotContains(response, self.early.title)

    def test_search_column_name_selects_the_category_and_filters_results(self) -> None:
        """导航使用栏目名称时查询页选中该栏目且只显示其公开文章。"""
        response = self.client.get(reverse("content:search"), {"category": self.news.name})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].cleaned_data["category"], self.news)
        self.assertContains(response, 'value="交大头条" selected')
        self.assertContains(response, self.early.title)
        self.assertNotContains(response, self.equal_second.title)

    def test_search_end_date_includes_the_entire_shanghai_day(self) -> None:
        """结束日期按上海自然日闭区间解释。"""
        response = self.client.get(
            reverse("content:search"),
            {"start": "2026-08-13", "end": "2026-08-13"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.early.title)
        self.assertNotContains(response, self.equal_first.title)

    def test_search_invalid_category_does_not_run_public_content_query(self) -> None:
        """不存在的栏目主键由表单拒绝并返回可修正页面。"""
        with self.assertNumQueries(2):
            response = self.client.get(reverse("content:search"), {"category": "999999"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "选择一个有效的选项")
        self.assertNotContains(response, self.early.title)

    def test_public_pages_hide_drafts(self) -> None:
        """首页、列表、搜索和详情都不暴露草稿。"""
        for url in (
            reverse("content:index"),
            reverse("content:search"),
        ):
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), self.draft.title)

        self.assertEqual(
            self.client.get(reverse("content:item_detail", args=[self.draft.pk])).status_code,
            404,
        )

    def test_search_uses_primary_key_as_stable_tiebreaker_for_equal_publish_times(self) -> None:
        """相同发表时间的分页排序以主键倒序稳定收束。"""
        response = self.client.get(reverse("content:search"))
        body = response.content.decode()

        self.assertLess(body.index(self.equal_second.title), body.index(self.equal_first.title))

    def test_homepage_exposes_bounded_grouped_sections(self) -> None:
        """首页提供有界最新文章及按栏目聚合的公开内容。"""
        response = self.client.get(reverse("content:index"))

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.context["latest_items"]), 24)
        self.assertIn("grouped_items", response.context)
        self.assertEqual(
            {item.category_id for item in response.context["latest_items"]},
            {self.news.pk, self.notice.pk},
        )


@override_settings(PUBLIC_PAGE_CACHE_ENABLED=False)
class PublicQueryBudgetTests(TestCase):
    """锁定公开页面的查询预算，防止模板引入 N+1。"""

    @classmethod
    def setUpTestData(cls) -> None:
        categories = [
            Category.objects.create(name=f"栏目 {index}", description="演示栏目")
            for index in range(1, 5)
        ]
        for index in range(24):
            Item.objects.create(
                title=f"公开文章 {index:02d}",
                content="content",
                category=categories[index % len(categories)],
                publish_time=datetime(2026, 8, 1 + index % 10, 9, tzinfo=SHANGHAI),
                is_published=True,
            )
        Item.objects.create(
            title="查询预算草稿",
            content="draft",
            category=categories[0],
            is_published=False,
        )

    def test_homepage_stays_within_one_query(self) -> None:
        """首页文章分组由一次预加载查询完成。"""
        with self.assertNumQueries(1):
            response = self.client.get(reverse("content:index"))

        self.assertEqual(response.status_code, 200)

    def test_search_without_filters_stays_within_three_queries(self) -> None:
        """无条件文章查询只执行栏目选项、计数和当前页查询。"""
        with self.assertNumQueries(3):
            response = self.client.get(reverse("content:search"))

        self.assertEqual(response.status_code, 200)

    def test_search_stays_within_three_queries(self) -> None:
        """组合搜索只执行栏目选项、计数和当前页查询。"""
        with self.assertNumQueries(3):
            response = self.client.get(reverse("content:search"), {"q": "公开"})

        self.assertEqual(response.status_code, 200)
