"""前台文章结果页面呈现测试。"""

from django.urls import reverse

from content.tests.test_views import BaseViewTests


class SearchPresentationTests(BaseViewTests):
    def test_search_has_help_and_clear_route(self):
        response = self.client.get(reverse("content:search"))
        self.assertContains(response, 'id="id_start_helptext"')
        self.assertContains(response, 'aria-describedby="id_start_helptext"')
        self.assertContains(response, 'aria-describedby="id_end_helptext"')
        self.assertContains(response, 'for="id_q"')
        self.assertContains(response, reverse("content:search"))

    def test_search_without_filters_explains_result_scope(self):
        response = self.client.get(reverse("content:search"))
        self.assertContains(response, 'class="condition-summary"')
        self.assertContains(response, "显示全部已发布文章")

    def test_empty_result_has_status_and_restore_route(self):
        response = self.client.get(
            reverse("content:search"), {"q": "不存在的关键词xyz"}
        )
        self.assertContains(response, 'role="status"')
        self.assertContains(response, reverse("content:item_list"))

    def test_category_list_exposes_context(self):
        response = self.client.get(
            reverse("content:item_list"), {"category": self.cat_python.pk}
        )
        self.assertContains(response, 'class="current-context"')
