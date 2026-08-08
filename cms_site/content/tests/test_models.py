"""模型层单元测试（对应《测试文档》§6.1 T-MD-01~06）。

覆盖：
- T-MD-01 Category 创建与 __str__
- T-MD-02 Category 名称唯一约束
- T-MD-03 Item 必填约束（无栏目拒绝）
- T-MD-04 PROTECT 删除保护（裁决 D-3'：有文章栏目禁删，抛 ProtectedError）
- T-MD-05 默认排序（publish_time 倒序）
- T-MD-06 默认发布状态（is_published=True）
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from content.models import Category, Item


class CategoryModelTests(TestCase):
    """T-MD-01 / T-MD-02：Category 创建与唯一约束。"""

    def test_tmd01_create_category_and_str(self):
        """T-MD-01：创建栏目，__str__ 返回名称。"""
        cat = Category.objects.create(name="教学动态", description="教学相关")
        self.assertEqual(str(cat), "教学动态")
        self.assertIsNotNone(cat.created_at)

    def test_tmd02_name_unique_rejected(self):
        """T-MD-02：同名栏目触发唯一约束（数据库层 IntegrityError）。"""
        Category.objects.create(name="教学动态")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name="教学动态")

    def test_tmd02b_name_unique_case_sensitive_default(self):
        """T-MD-02 补充：不同名不受影响。"""
        Category.objects.create(name="教学动态")
        cat2 = Category.objects.create(name="科研进展")
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(str(cat2), "科研进展")


class ItemModelTests(TestCase):
    """T-MD-03 / T-MD-04 / T-MD-05 / T-MD-06：Item 约束、删除保护、排序、默认状态。"""

    def setUp(self):
        self.cat = Category.objects.create(name="教学动态")

    def test_tmd03_item_requires_category(self):
        """T-MD-03：无栏目创建文章被拒绝（数据库非空外键约束）。"""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Item.objects.create(title="无栏目文章", content="正文")

    def test_tmd04_delete_protected_when_items_exist(self):
        """T-MD-04：栏目下存在文章时删除 → ProtectedError，栏目保留。"""
        Item.objects.create(title="文章1", content="正文", category=self.cat)
        with self.assertRaises(ProtectedError):
            self.cat.delete()
        self.assertTrue(Category.objects.filter(pk=self.cat.pk).exists())

    def test_tmd04b_delete_empty_category_succeeds(self):
        """T-MD-04 补充：空栏目可删除。"""
        empty = Category.objects.create(name="空栏目")
        empty.delete()
        self.assertFalse(Category.objects.filter(pk=empty.pk).exists())

    def test_tmd05_default_ordering_by_publish_time_desc(self):
        """T-MD-05：默认按 publish_time 倒序。"""
        old = Item.objects.create(title="旧文章", content="正文", category=self.cat,
                                  publish_time=timezone.now() - timedelta(days=10))
        new = Item.objects.create(title="新文章", content="正文", category=self.cat,
                                  publish_time=timezone.now())
        self.assertEqual(list(Item.objects.all()), [new, old])

    def test_tmd06_default_is_published_true(self):
        """T-MD-06：默认 is_published=True。"""
        item = Item.objects.create(title="默认发布", content="正文", category=self.cat)
        self.assertTrue(item.is_published)

    def test_tmd06b_publish_time_default_auto_now_add(self):
        """T-MD-06 补充：publish_time 默认值自动填充为当前时间。"""
        item = Item.objects.create(title="时间默认", content="正文", category=self.cat)
        self.assertIsNotNone(item.publish_time)
        self.assertLessEqual(item.publish_time, timezone.now())

    def test_tmd07_author_optional(self):
        """T-MD-07 补充：author 可空（FR-ART-01 扩展）。"""
        user = get_user_model().objects.create_user(username="writer", password="x12345678")
        item = Item.objects.create(title="有作者", content="正文", category=self.cat, author=user)
        self.assertEqual(item.author, user)
