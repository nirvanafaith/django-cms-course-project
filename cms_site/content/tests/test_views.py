"""视图/路由/模板链路集成测试（对应《测试文档》§6.3 T-IT-01~16）。

覆盖：
- T-IT-01~05 首页/列表/详情/404/草稿不可见
- T-IT-06~12 三种查询模式 + 组合 + 非法输入不 500
- T-IT-13~16 分页守卫与条件保持
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Category, Item


class BaseViewTests(TestCase):
    """公共夹具：栏目与文章数据。"""

    @classmethod
    def setUpTestData(cls):
        cls.cat_python = Category.objects.create(name="教学动态")
        cls.cat_notice = Category.objects.create(name="通知公告")
        cls.item1 = Item.objects.create(
            title="Python 课程通知",
            content="2026 年春季 Python 课程安排",
            category=cls.cat_python,
            publish_time=timezone.now() - timedelta(days=1),
        )
        cls.item2 = Item.objects.create(
            title="教学会议通知",
            content="下周召开教学会议",
            category=cls.cat_python,
            publish_time=timezone.now() - timedelta(days=2),
        )
        cls.item3 = Item.objects.create(
            title="失物招领公告",
            content="捡到学生卡一张",
            category=cls.cat_notice,
            publish_time=timezone.now() - timedelta(days=3),
        )
        cls.draft = Item.objects.create(
            title="草稿文章不可见",
            content="草稿内容",
            category=cls.cat_python,
            is_published=False,
            publish_time=timezone.now(),
        )


class BrowseViewTests(BaseViewTests):
    """T-IT-01~05：前台浏览。"""

    def test_tit01_index_200_contains_nav_and_latest(self):
        """T-IT-01：首页 200，含栏目导航与最新文章标题。"""
        resp = self.client.get(reverse("content:index"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "教学动态")
        self.assertContains(resp, "Python 课程通知")

    def test_tit02_category_list_filter(self):
        """T-IT-02：/list/?category=id 仅显示该栏目文章。"""
        resp = self.client.get(
            reverse("content:item_list"), {"category": self.cat_python.pk}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Python 课程通知")
        self.assertContains(resp, "教学会议通知")
        self.assertNotContains(resp, "失物招领公告")

    def test_tit03_detail_200(self):
        """T-IT-03：详情页 200，含标题/正文。"""
        resp = self.client.get(reverse("content:item_detail", args=[self.item1.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Python 课程通知")
        self.assertContains(resp, "2026 年春季 Python 课程安排")

    def test_tit04_detail_404(self):
        """T-IT-04：不存在 pk → 404。"""
        resp = self.client.get(reverse("content:item_detail", args=[99999]))
        self.assertEqual(resp.status_code, 404)

    def test_tit05_draft_invisible_everywhere(self):
        """T-IT-05：草稿在详情/列表/首页三种入口均不可见。"""
        # 详情 → 404
        resp = self.client.get(reverse("content:item_detail", args=[self.draft.pk]))
        self.assertEqual(resp.status_code, 404)
        # 列表 → 不出现
        resp = self.client.get(
            reverse("content:item_list"), {"category": self.cat_python.pk}
        )
        self.assertNotContains(resp, "草稿文章不可见")
        # 首页 → 不出现
        resp = self.client.get(reverse("content:index"))
        self.assertNotContains(resp, "草稿文章不可见")


class SearchViewTests(BaseViewTests):
    """T-IT-06~12：三种查询模式 + 组合 + 健壮性。"""

    def test_tit06_search_by_title(self):
        """T-IT-06：按题目 q=Python 仅命中含关键词标题。"""
        resp = self.client.get(reverse("content:search"), {"q": "Python"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Python 课程通知")
        self.assertNotContains(resp, "失物招领公告")

    def test_tit07_search_no_result(self):
        """T-IT-07：无结果返回 200 + 空提示。"""
        resp = self.client.get(reverse("content:search"), {"q": "不存在的关键词xyz"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "没有找到")

    def test_tit08_search_by_time_range(self):
        """T-IT-08：时间范围查询，结果均在范围内。

        边界取自已存储的 item2.publish_time 日期（避免 setUpTestData 与执行间的时钟漂移）。
        """
        start = self.item2.publish_time.date()
        end = self.item2.publish_time.date()
        resp = self.client.get(
            reverse("content:search"),
            {"start": start.isoformat(), "end": end.isoformat()},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "教学会议通知")  # 当日
        self.assertNotContains(resp, "Python 课程通知")  # 次日，超出 end
        self.assertNotContains(resp, "失物招领公告")  # 前一日，早于 start

    def test_tit09_search_start_only(self):
        """T-IT-09：仅 start，结果 ≥ start（边界取自已存储的 item1 日期）。"""
        start = self.item1.publish_time.date()
        resp = self.client.get(reverse("content:search"), {"start": start.isoformat()})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Python 课程通知")  # 当日
        self.assertNotContains(resp, "失物招领公告")  # 早于 start

    def test_tit10_search_by_category(self):
        """T-IT-10：按栏目查询，与该栏目文章一致。"""
        resp = self.client.get(
            reverse("content:search"), {"category": self.cat_python.pk}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Python 课程通知")
        self.assertContains(resp, "教学会议通知")
        self.assertNotContains(resp, "失物招领公告")

    def test_tit11_combined_query(self):
        """T-IT-11：组合查询（q + category）三条件交集。"""
        resp = self.client.get(
            reverse("content:search"),
            {"q": "Python", "category": self.cat_python.pk},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Python 课程通知")  # 满足 q + 栏目
        self.assertNotContains(resp, "教学会议通知")  # 不含"Python"
        self.assertNotContains(resp, "失物招领公告")  # 栏目不符

    def test_tit12_invalid_date_no_500(self):
        """T-IT-12：非法日期返回 200 + 错误提示回显，而非 500。"""
        resp = self.client.get(reverse("content:search"), {"start": "2026-13-45"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "日期格式应为 YYYY-MM-DD")


class PaginationTests(BaseViewTests):
    """T-IT-13~16：分页守卫与条件保持。"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # 补足 25 篇文章用于分页（T-IT-13）
        for i in range(22):
            Item.objects.create(
                title=f"分页文章-{i:02d}",
                content="正文",
                category=cls.cat_python,
                publish_time=timezone.now() - timedelta(days=10 + i),
            )

    def test_tit13_pagination_page3(self):
        """T-IT-13：25 篇、每页 10 条 → 共 3 页，第 3 页 5 条（17~21 号）。"""
        resp = self.client.get(reverse("content:search"), {"page": 3})
        self.assertEqual(resp.status_code, 200)
        # 第 3 页为最后 5 条：分页文章-17 ~ 分页文章-21
        self.assertContains(resp, "分页文章-21")
        self.assertContains(resp, "分页文章-17")
        self.assertNotContains(resp, "分页文章-16")  # 第 2 页末条
        self.assertContains(resp, "共 3 页")

    def test_tit14_bad_page_values(self):
        """T-IT-14：page=0/-1/abc 全部回退第 1 页且 200。"""
        for bad in ("0", "-1", "abc"):
            resp = self.client.get(reverse("content:search"), {"page": bad})
            self.assertEqual(resp.status_code, 200, msg=f"page={bad}")

    def test_tit15_page_out_of_range(self):
        """T-IT-15：page=99 超界回退末页且 200。"""
        resp = self.client.get(reverse("content:search"), {"page": 99})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "共 3 页")

    def test_tit16_pagination_keeps_query(self):
        """T-IT-16：翻页链接保留查询条件。

        用命中多条结果的词（q=文章，22 条 → 3 页），断言分页链接带 q 参数。
        """
        resp = self.client.get(reverse("content:search"), {"q": "文章"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "共 3 页")  # 确保有分页
        # 分页链接应带 q 参数（URL 编码后）
        self.assertContains(resp, "q=%E6%96%87%E7%AB%A0")
