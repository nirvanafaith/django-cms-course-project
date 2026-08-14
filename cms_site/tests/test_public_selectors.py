"""公开内容 selector 合同测试。"""

from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from content.models import Category, Item
from content.selectors import homepage_items, search_published_items

SHANGHAI = ZoneInfo("Asia/Shanghai")


class PublicSelectorTests(TestCase):
    """验证 selector 只返回有界、已发布且按业务语义筛选的文章。"""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.category = Category.objects.create(name="selector 栏目", description="selector")
        Item.objects.create(
            title="selector 已发布文章",
            content="published",
            category=cls.category,
            publish_time=datetime(2026, 8, 13, 9, tzinfo=SHANGHAI),
            is_published=True,
        )
        Item.objects.create(
            title="selector 草稿文章",
            content="draft",
            category=cls.category,
            publish_time=datetime(2026, 8, 14, 9, tzinfo=SHANGHAI),
            is_published=False,
        )

    def test_homepage_items_are_bounded_and_hide_drafts(self) -> None:
        """首页 selector 尊重显式上限并排除草稿。"""
        items = tuple(homepage_items(limit=1))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "selector 已发布文章")

    def test_search_selector_uses_inclusive_shanghai_date_end(self) -> None:
        """搜索 selector 的结束日期包含上海自然日当天文章。"""
        items = tuple(
            search_published_items(
                keyword="已发布",
                start=datetime(2026, 8, 13, tzinfo=SHANGHAI).date(),
                end=datetime(2026, 8, 13, tzinfo=SHANGHAI).date(),
                category=self.category,
            )
        )

        self.assertEqual([item.title for item in items], ["selector 已发布文章"])
