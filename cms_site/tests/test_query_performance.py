"""PostgreSQL 内容查询索引与规模验证。"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import connection
from django.test import TestCase, tag

from content.models import Category, Item
from content.selectors import search_published_items

SHANGHAI = ZoneInfo("Asia/Shanghai")


@tag("postgres_performance")
class PostgreSQLQueryPerformanceTests(TestCase):
    """在扩展数据集上验证公开查询可以使用计划中的索引。"""

    @classmethod
    def setUpTestData(cls) -> None:
        target_index = 9_991
        categories = [
            Category(name=f"性能验证栏目 {index}", description="索引计划验证")
            for index in range(10)
        ]
        Category.objects.bulk_create(categories)
        cls.category = Category.objects.get(name=f"性能验证栏目 {target_index % len(categories)}")
        items = [
            Item(
                title=(
                    "唯一性能索引验证标识" if index == target_index else f"常规公开内容 {index:05d}"
                ),
                content="performance",
                category=categories[index % len(categories)],
                publish_time=datetime(2024, 1, 1, 9, tzinfo=SHANGHAI) + timedelta(minutes=index),
                is_published=index % 97 == 0,
            )
            for index in range(10_000)
        ]
        Item.objects.bulk_create(items, batch_size=1_000)
        with connection.cursor() as cursor:
            cursor.execute("ANALYZE content_item")

    def test_category_time_query_exposes_composite_index(self) -> None:
        """栏目公开列表的执行计划包含复合 B-tree 索引名称。"""
        plan = search_published_items(category=self.category).explain(analyze=False)

        self.assertIn("item_cat_pub_time_idx", plan)

    def test_title_query_exposes_trigram_index(self) -> None:
        """标题包含查询的执行计划包含 Trigram GIN 索引名称。"""
        plan = search_published_items(keyword="唯一性能索引验证标识").explain(analyze=False)

        self.assertIn("item_title_trgm_idx", plan)
