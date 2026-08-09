"""文章 QuerySet 的单元测试。

这里直接使用 Django 测试数据库中的真实模型，不使用模拟对象。测试关注公开
查询接口的行为：前台可见性规则是否排除草稿，以及返回值能否继续链式过滤。
"""

from django.test import TestCase

from content.models import Category, Item


class ItemQuerySetTests(TestCase):
    """验证文章查询集合提供的可复用业务规则。"""

    @classmethod
    def setUpTestData(cls):
        """Given：为本测试类建立一篇已发布文章和一篇草稿。"""
        category = Category.objects.create(name="测试栏目")
        cls.published_item = Item.objects.create(title="已发布", category=category)
        Item.objects.create(title="草稿", category=category, is_published=False)

    def test_published_excludes_drafts(self):
        """When 查询公开文章，Then 结果不包含草稿。"""
        items = Item.objects.published()

        self.assertQuerySetEqual(items, [self.published_item])

    def test_published_remains_chainable(self):
        """When 在公开文章后继续过滤，Then QuerySet 链式调用仍然有效。"""
        item_exists = Item.objects.published().filter(title__contains="已发布").exists()

        self.assertTrue(item_exists)
