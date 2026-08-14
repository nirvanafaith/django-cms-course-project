"""公开登录、退出与角色导航测试。"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AuthenticationFlowTests(TestCase):
    """验证匿名、普通用户和管理员的可见入口。"""

    normal_user: User
    superuser: User

    @classmethod
    def setUpTestData(cls) -> None:
        """创建两种可见角色。"""
        cls.normal_user = User.objects.create_user(
            username="student",
            password="test-password-1",
        )
        cls.superuser = User.objects.create_superuser(
            username="cms-admin",
            email="admin@example.com",
            password="test-password-2",
        )

    def test_anonymous_user_can_open_login_page(self) -> None:
        """匿名访问登录页会获得可提交表单。"""
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertContains(response, 'class="field-group"', count=2)

    def test_normal_user_logs_in_without_admin_navigation(self) -> None:
        """普通用户登录后只能看到公开功能。"""
        logged_in = self.client.login(username="student", password="test-password-1")

        response = self.client.get(reverse("content:index"))

        self.assertTrue(logged_in)
        self.assertContains(response, "退出登录")
        self.assertNotContains(response, "管理后台")

    def test_superuser_logs_in_with_admin_navigation(self) -> None:
        """超级用户登录后看到管理后台入口。"""
        logged_in = self.client.login(username="cms-admin", password="test-password-2")

        response = self.client.get(reverse("content:index"))

        self.assertTrue(logged_in)
        self.assertContains(response, "管理后台")

    def test_post_logout_ends_session(self) -> None:
        """退出必须通过 POST 并清除认证会话。"""
        self.client.force_login(self.normal_user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("content:index"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_normal_user_cannot_enter_admin(self) -> None:
        """隐藏入口之外，Admin 服务端仍拒绝普通用户。"""
        self.client.force_login(self.normal_user)

        response = self.client.get(reverse("admin:index"))

        self.assertRedirects(response, f"{reverse('admin:login')}?next={reverse('admin:index')}")
