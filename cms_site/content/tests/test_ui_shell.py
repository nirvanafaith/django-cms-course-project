"""全局页面壳与导航可访问性测试。"""

from django.contrib.auth import get_user_model
from django.urls import reverse

from content.tests.test_views import BaseViewTests


class ShellAccessibilityTests(BaseViewTests):
    def test_index_has_skip_link_and_landmarks(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, 'href="#main-content"')
        self.assertContains(response, 'id="main-content"')
        self.assertContains(response, 'aria-label="主导航"')

    def test_mobile_toggle_exposes_state(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, 'aria-controls="site-nav-menu"')

    def test_admin_link_is_staff_only(self):
        self.assertNotContains(
            self.client.get(reverse("content:index")), 'href="/admin/"'
        )
        user = get_user_model().objects.create_user(
            username="staff-ui", password="pass12345", is_staff=True
        )
        self.client.force_login(user)
        self.assertContains(
            self.client.get(reverse("content:index")), 'href="/admin/"'
        )
