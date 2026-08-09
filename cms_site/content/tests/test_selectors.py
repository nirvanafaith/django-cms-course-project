"""前台只读查询 selector 的集成测试。

测试使用真实 Django ORM 和临时测试数据库，验证 selector 返回的数据集合，而
不是绑定具体 SQL 文本。这样既能保护业务规则，也允许 Django 调整 SQL 细节。
"""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from content.models import Category, Item
from content.selectors import (
    categories_with_item_counts,
    latest_published_items,
    published_item_by_pk,
    published_items_for_category,
    search_published_items,
)


class SelectorTests(TestCase):
    """验证前台浏览和搜索所需的只读查询规则。"""

    @classmethod
    def setUpTestData(cls):
        """Given：建立跨栏目、跨日期且同时包含草稿的固定数据。"""
        cls.category = Category.objects.create(name="教学动态")
        cls.other_category = Category.objects.create(name="通知公告")
        cls.reference_time = timezone.now().replace(microsecond=0)
        cls.target = Item.objects.create(
            title="Python 课程",
            category=cls.category,
            publish_time=cls.reference_time,
        )
        cls.draft = Item.objects.create(
            title="Python 草稿",
            category=cls.category,
            publish_time=cls.reference_time,
            is_published=False,
        )
        cls.old_notice = Item.objects.create(
            title="旧公告",
            category=cls.other_category,
            publish_time=cls.reference_time - timedelta(days=1),
        )

    def test_category_count_counts_only_published_items(self):
        """When 获取前台栏目计数，Then 草稿不计入公开文章数量。"""
        category = categories_with_item_counts().get(pk=self.category.pk)

        self.assertEqual(category.item_count, 1)

    def test_latest_items_are_published_and_limitable(self):
        """When 限制最新文章为一篇，Then 返回最新的已发布文章。"""
        items = list(latest_published_items(limit=1))

        self.assertEqual(items, [self.target])

    def test_latest_items_load_category_in_same_query(self):
        """When 遍历文章及栏目，Then select_related 让读取只执行一条 SQL。"""
        with self.assertNumQueries(1):
            category_names = [item.category.name for item in latest_published_items()]

        self.assertEqual(category_names, ["教学动态", "通知公告"])

    def test_category_selector_filters_published_items(self):
        """When 按栏目查询，Then 只返回该栏目的已发布文章。"""
        items = published_items_for_category(self.category.pk)

        self.assertQuerySetEqual(items, [self.target])

    def test_category_selector_without_id_returns_all_published_items(self):
        """When 未指定栏目，Then 返回所有栏目中的已发布文章。"""
        items = published_items_for_category()

        self.assertQuerySetEqual(items, [self.target, self.old_notice])

    def test_detail_selector_hides_draft(self):
        """When 按主键读取草稿，Then selector 按不存在处理。"""
        with self.assertRaises(Item.DoesNotExist):
            published_item_by_pk(self.draft.pk)

    def test_search_combines_keyword_date_and_category(self):
        """When 同时提供三类条件，Then 查询使用 AND 语义命中交集。"""
        items = search_published_items(
            keyword="Python",
            start=self.reference_time.date(),
            end=self.reference_time.date(),
            category=self.category,
        )

        self.assertQuerySetEqual(items, [self.target])

    def test_search_end_date_includes_the_whole_day(self):
        """When 结束日期等于文章日期，Then 当天非零点文章仍被包含。"""
        items = search_published_items(end=self.reference_time.date())

        self.assertIn(self.target, items)
