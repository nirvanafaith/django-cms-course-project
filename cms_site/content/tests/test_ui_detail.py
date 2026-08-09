"""文章详情与组件状态夹具测试。"""

from django.template.loader import render_to_string
from django.test import TestCase
from django.urls import reverse

from content.tests.test_views import BaseViewTests


class ArticleDetailPresentationTests(BaseViewTests):
    def test_detail_has_semantic_reading_structure(self):
        response = self.client.get(
            reverse("content:item_detail", args=[self.item1.pk])
        )
        self.assertContains(response, 'aria-label="面包屑"')
        self.assertContains(response, 'class="article-content"')
        self.assertContains(response, reverse("content:item_list"))


class ComponentShowcaseTests(TestCase):
    def test_showcase_exposes_required_state_markers(self):
        html = render_to_string("content/_showcase.html")
        for marker in (
            "state-default",
            "state-hover",
            "state-focus",
            "state-disabled",
            "state-error",
            "state-empty",
        ):
            self.assertIn(marker, html)
