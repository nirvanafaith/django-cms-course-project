"""系统/端到端测试（对应《测试文档》§6.5 T-SYS-01~04）。

覆盖：
- T-SYS-01 种子数据可复现（seed_data 幂等：执行两次数目一致）
- T-SYS-02 发布闭环（建栏目→发文章→前台可见→修改→删除）
- T-SYS-03 查询闭环（三种模式命中同一目标）
- T-SYS-04 组合+分页闭环（页间不重不漏）
"""

from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Category, Item


class SeedDataTests(TestCase):
    """T-SYS-01：seed_data 幂等可复现。"""

    def test_tsys01_seed_data_idempotent(self):
        """空库执行 seed_data 两次：栏目 5 个、文章 ≥50，两次数目一致。"""
        call_command("seed_data")
        first_cats = Category.objects.count()
        first_items = Item.objects.count()
        self.assertEqual(first_cats, 5)
        self.assertGreaterEqual(first_items, 50)

        call_command("seed_data")  # 第二次执行
        self.assertEqual(Category.objects.count(), first_cats)
        self.assertEqual(Item.objects.count(), first_items)

    def test_tsys01b_seed_data_has_unpublished_and_time_spread(self):
        """T-SYS-01 补充：种子数据含草稿（验证前台过滤）且时间跨年。"""
        call_command("seed_data")
        self.assertTrue(Item.objects.filter(is_published=False).exists())
        years = {i.publish_time.year for i in Item.objects.all()}
        self.assertGreaterEqual(len(years), 2)  # 时间分布跨年（2023~2026）


class PublishCycleTests(TestCase):
    """T-SYS-02：发布闭环（管理端→前台）。"""

    def test_tsys02_publish_close_loop(self):
        """建栏目→发文章→前台可见→改标题→前台更新→删文章→前台消失。"""
        cat = Category.objects.create(name="闭环栏目")
        item = Item.objects.create(
            title="初始标题",
            content="正文",
            category=cat,
            publish_time=timezone.now(),
        )
        # 前台可见
        self.assertContains(self.client.get(reverse("content:index")), "初始标题")
        # 修改
        item.title = "更新后标题"
        item.save()
        resp = self.client.get(reverse("content:index"))
        self.assertContains(resp, "更新后标题")
        self.assertNotContains(resp, "初始标题")
        # 删除 → 前台消失
        pk = item.pk
        item.delete()
        self.assertEqual(
            self.client.get(reverse("content:item_detail", args=[pk])).status_code, 404
        )


class QueryLoopTests(TestCase):
    """T-SYS-03：查询闭环（三种模式命中同一目标）。"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name="教学动态")
        cls.target = Item.objects.create(
            title="Python 程序设计课程公告",
            content="正文",
            category=cls.cat,
            publish_time=timezone.now() - timedelta(days=5),
        )

    def test_tsys03_three_modes_hit_same_target(self):
        """按题目 / 按时间 / 按栏目 三种方式均命中目标文章。"""
        # 按题目
        resp = self.client.get(reverse("content:search"), {"q": "Python"})
        self.assertContains(resp, "Python 程序设计课程公告")
        # 按时间（目标文章当天）
        day = self.target.publish_time.date().isoformat()
        resp = self.client.get(reverse("content:search"), {"start": day, "end": day})
        self.assertContains(resp, "Python 程序设计课程公告")
        # 按栏目
        resp = self.client.get(reverse("content:search"), {"category": self.cat.pk})
        self.assertContains(resp, "Python 程序设计课程公告")


class CombinedPaginationTests(TestCase):
    """T-SYS-04：组合 + 分页闭环（页间不重不漏）。"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name="分页栏目")
        for i in range(25):
            Item.objects.create(
                title=f"组合文章-{i:02d}",
                content="正文",
                category=cls.cat,
                publish_time=timezone.now() - timedelta(days=i),
            )

    def test_tsys04_combined_pagination_no_overlap(self):
        """组合查询（栏目 + 关键词）分页，页间不重不漏。"""
        ids_page1 = self._page_ids(1)
        ids_page2 = self._page_ids(2)
        ids_page3 = self._page_ids(3)
        self.assertEqual(len(ids_page1), 10)
        self.assertEqual(len(ids_page2), 10)
        self.assertEqual(len(ids_page3), 5)
        all_ids = ids_page1 | ids_page2 | ids_page3
        self.assertEqual(len(all_ids), 25)  # 不重不漏

    def _page_ids(self, page):
        resp = self.client.get(
            reverse("content:search"),
            {"category": self.cat.pk, "q": "组合文章", "page": page},
        )
        self.assertEqual(resp.status_code, 200)
        ids = set()
        for item in resp.context["page_obj"]:
            ids.add(item.pk)
        return ids
