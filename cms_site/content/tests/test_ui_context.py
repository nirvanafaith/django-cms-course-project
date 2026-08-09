"""查询上下文与表单呈现契约测试。"""

from django.urls import reverse

from content.tests.test_views import BaseViewTests


class CategoryContextTests(BaseViewTests):
    def test_item_list_exposes_current_category(self):
        response = self.client.get(
            reverse("content:item_list"), {"category": self.cat_python.pk}
        )
        self.assertEqual(response.context["current_category"], self.cat_python)

    def test_search_exposes_selected_category(self):
        response = self.client.get(
            reverse("content:search"), {"category": self.cat_python.pk}
        )
        self.assertEqual(response.context["current_category"], self.cat_python)


class SearchFormPresentationTests(BaseViewTests):
    def test_category_filter_has_unfiltered_option(self):
        response = self.client.get(reverse("content:search"))
        choices = list(response.context["form"].fields["category"].choices)
        self.assertEqual(choices[0], ("", "全部栏目"))

    def test_invalid_date_keeps_help_and_error_associations(self):
        response = self.client.get(
            reverse("content:search"), {"start": "2026-13-45"}
        )
        self.assertContains(
            response,
            'aria-describedby="id_start_helptext id_start_error"',
        )
