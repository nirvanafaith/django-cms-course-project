"""PostgreSQL 文章模型合同测试。"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from content.models import Category, Item


class ItemMetadataTests(TestCase):
    """验证文章默认值、校验规则和 PostgreSQL 索引声明。"""

    category: Category

    def setUp(self) -> None:
        """创建每个模型测试使用的栏目。"""
        self.category = Category.objects.create(name="测试栏目")

    def test_new_item_defaults_to_draft(self) -> None:
        """新文章未经管理员操作时保持草稿。"""
        item = Item(title="草稿", content="正文", category=self.category)

        self.assertFalse(item.is_published)

    def test_blank_content_fails_model_validation(self) -> None:
        """空正文不能通过模型完整校验。"""
        item = Item(title="无正文", content="", category=self.category)

        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_orders_by_publish_time_and_primary_key(self) -> None:
        """相同发表时间使用主键形成稳定次序。"""
        self.assertEqual(Item._meta.ordering, ["-publish_time", "-pk"])

    def test_declares_postgresql_query_indexes(self) -> None:
        """模型声明首页、栏目和标题包含查询索引。"""
        names = {index.name for index in Item._meta.indexes}

        self.assertEqual(
            names,
            {"item_pub_time_idx", "item_cat_pub_time_idx", "item_title_trgm_idx"},
        )


class ItemRelationshipTests(TestCase):
    """验证栏目与作者删除策略。"""

    author: User
    category: Category
    item: Item

    def setUp(self) -> None:
        """创建持久化文章及其关系对象。"""
        self.category = Category.objects.create(name="关系栏目")
        self.author = User.objects.create_user(username="author")
        self.item = Item.objects.create(
            title="关系测试",
            content="正文",
            category=self.category,
            author=self.author,
        )

    def test_protects_category_with_items(self) -> None:
        """仍有文章的栏目不可删除。"""
        with self.assertRaises(ProtectedError):
            _ = self.category.delete()

    def test_clears_author_when_user_is_deleted(self) -> None:
        """删除作者后历史文章继续保留。"""
        _ = self.author.delete()
        self.item.refresh_from_db()

        self.assertIsNone(self.item.author)
