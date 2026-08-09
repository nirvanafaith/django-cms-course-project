"""前台首页呈现测试。"""

from django.test import TestCase
from django.urls import reverse

from content.tests.test_views import BaseViewTests


class HomepagePresentationTests(BaseViewTests):
    def test_homepage_has_primary_routes(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, reverse("content:item_list"))
        self.assertContains(response, reverse("content:search"))
        self.assertContains(response, f"?category={self.cat_python.pk}")


class HomepageEmptyStateTests(TestCase):
    def test_empty_homepage_exposes_status_regions(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, 'role="status"', count=2)
