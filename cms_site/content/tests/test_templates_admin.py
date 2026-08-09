"""Django Admin 视觉覆盖契约测试。"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from content.models import Category, Item


class AdminTemplatePresentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="admin-ui", password="pass12345", is_staff=True
        )
        permissions = Permission.objects.filter(content_type__app_label="content")
        cls.user.user_permissions.add(*permissions)

    def setUp(self):
        self.client.force_login(self.user)

    def test_admin_index_loads_project_stylesheet(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "css/admin.css")

    def test_admin_item_page_keeps_native_actions(self):
        category = Category.objects.create(name="测试栏目")
        Item.objects.create(title="测试文章", category=category)
        response = self.client.get("/admin/content/item/")
        self.assertContains(response, "设为已发布")
        self.assertContains(response, "设为草稿")
