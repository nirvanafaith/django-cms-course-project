"""用户、内容与审计 Admin 集成测试。"""

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from content.admin import CategoryAdmin
from content.admin_forms import ItemAdminForm
from content.models import Category, Item
from core.admin import LogEntryAdmin
from core.admin_forms import CmsUserChangeForm, CmsUserCreationForm


class UserRoleFormTests(TestCase):
    """验证普通用户与管理员角色同步。"""

    def test_creation_form_builds_normal_user(self) -> None:
        """普通角色不会获得后台或超级用户标志。"""
        form = CmsUserCreationForm(
            data={
                "username": "student",
                "password1": "Complex-pass-2026",
                "password2": "Complex-pass-2026",
                "role": "normal",
                "is_active": True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_creation_form_builds_admin_user(self) -> None:
        """管理员角色同时获得 staff 与 superuser 标志。"""
        form = CmsUserCreationForm(
            data={
                "username": "admin-user",
                "password1": "Complex-pass-2026",
                "password2": "Complex-pass-2026",
                "role": "admin",
                "is_active": True,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_change_form_demotes_and_disables_admin(self) -> None:
        """降级和停用通过同一保存边界持久化。"""
        user = User.objects.create_superuser("admin", password="test-password")
        form = CmsUserChangeForm(
            instance=user,
            data={
                "username": user.username,
                "password": user.password,
                "role": "normal",
                "is_active": False,
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        changed = form.save()
        self.assertFalse(changed.is_staff)
        self.assertFalse(changed.is_superuser)
        self.assertFalse(changed.is_active)

    def test_change_form_promotes_normal_user(self) -> None:
        """提升角色时同步后台与超级用户标志。"""
        user = User.objects.create_user("normal", password="test-password")
        form = CmsUserChangeForm(
            instance=user,
            data={
                "username": user.username,
                "password": user.password,
                "role": "admin",
                "is_active": True,
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        changed = form.save()
        self.assertTrue(changed.is_staff)
        self.assertTrue(changed.is_superuser)
        self.assertTrue(changed.is_active)


class ContentAdminTests(TestCase):
    """验证内容校验、聚合和批量审计。"""

    admin_user: User
    category: Category

    @classmethod
    def setUpTestData(cls) -> None:
        """创建管理员和栏目。"""
        cls.admin_user = User.objects.create_superuser("cms-admin", password="password")
        cls.category = Category.objects.create(name="Admin 测试")

    def test_item_form_rejects_whitespace_title(self) -> None:
        """纯空白标题不能进入数据库。"""
        form = ItemAdminForm(data={"title": "   ", "content": "正文", "category": self.category.pk})

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_item_form_rejects_whitespace_content(self) -> None:
        """纯空白正文不能进入数据库。"""
        form = ItemAdminForm(data={"title": "标题", "content": "   ", "category": self.category.pk})

        self.assertFalse(form.is_valid())
        self.assertIn("content", form.errors)

    def test_category_counts_use_one_query(self) -> None:
        """栏目文章数由一次聚合查询读取。"""
        Item.objects.create(title="文章", content="正文", category=self.category)
        request = RequestFactory().get("/admin/content/category/")
        request.user = self.admin_user
        category_admin = CategoryAdmin(Category, admin.site)

        with self.assertNumQueries(1):
            counts = [
                category_admin.article_count(item) for item in category_admin.get_queryset(request)
            ]

        self.assertEqual(counts, [1])

    def test_bulk_publish_updates_and_logs_each_item(self) -> None:
        """批量发布更新状态并为每篇文章创建审计记录。"""
        items = [
            Item.objects.create(title=f"文章 {index}", content="正文", category=self.category)
            for index in range(2)
        ]
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("admin:content_item_changelist"),
            {
                "action": "mark_published",
                "_selected_action": [item.pk for item in items],
                "index": "0",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Item.objects.filter(is_published=True).count(), 2)
        self.assertEqual(LogEntry.objects.filter(user=self.admin_user).count(), 2)

    def test_bulk_draft_updates_and_logs_each_item(self) -> None:
        """批量撤回更新状态并为每篇文章创建审计记录。"""
        items = [
            Item.objects.create(
                title=f"已发布文章 {index}",
                content="正文",
                category=self.category,
                is_published=True,
            )
            for index in range(2)
        ]
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("admin:content_item_changelist"),
            {
                "action": "mark_draft",
                "_selected_action": [item.pk for item in items],
                "index": "0",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Item.objects.filter(is_published=False).count(), 2)
        self.assertEqual(LogEntry.objects.filter(user=self.admin_user).count(), 2)


class AuditAdminTests(TestCase):
    """验证管理审计日志保持只读。"""

    def test_log_entry_admin_denies_all_mutations(self) -> None:
        """审计列表不能新增、修改或删除记录。"""
        request = RequestFactory().get("/admin/admin/logentry/")
        request.user = User.objects.create_superuser("auditor", password="password")
        log_admin = LogEntryAdmin(LogEntry, admin.site)

        self.assertFalse(log_admin.has_add_permission(request))
        self.assertFalse(log_admin.has_change_permission(request))
        self.assertFalse(log_admin.has_delete_permission(request))
        self.assertTrue(log_admin.has_view_permission(request))
