"""表单层单元测试（对应《测试文档》§6.2 T-FM-01~08）。

覆盖 SearchForm 校验规则：
- T-FM-01 空表单合法，全部字段为 None
- T-FM-02 标题关键词 strip 清洗
- T-FM-03 q 超长拒绝
- T-FM-04 / T-FM-05 非法日期/非日期字符串拒绝
- T-FM-06 起止日期顺序校验（start > end 拒绝）
- T-FM-07 非法栏目 id 拒绝
- T-FM-08 仅起始 / 仅结束各自合法
"""

from django.test import TestCase

from content.forms import SearchForm
from content.models import Category


class SearchFormTests(TestCase):
    """SearchForm 查询表单校验（T-FM-01~08）。"""

    def setUp(self):
        self.cat = Category.objects.create(name="教学动态")

    def test_tfm01_empty_form_valid(self):
        """T-FM-01：空表单合法，全部字段为 None。"""
        form = SearchForm({})
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["q"])
        self.assertIsNone(form.cleaned_data["start"])
        self.assertIsNone(form.cleaned_data["end"])
        self.assertIsNone(form.cleaned_data["category"])

    def test_tfm02_q_stripped(self):
        """T-FM-02：标题关键词去除首尾空白。"""
        form = SearchForm({"q": "  Python  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["q"], "Python")

    def test_tfm03_q_too_long_rejected(self):
        """T-FM-03：q 超过 100 字符拒绝。"""
        form = SearchForm({"q": "x" * 101})
        self.assertFalse(form.is_valid())
        self.assertIn("q", form.errors)

    def test_tfm04_invalid_date_rejected(self):
        """T-FM-04：非法日期（2026-13-45）拒绝。"""
        form = SearchForm({"start": "2026-13-45"})
        self.assertFalse(form.is_valid())
        self.assertIn("start", form.errors)

    def test_tfm05_non_date_string_rejected(self):
        """T-FM-05：非日期字符串（abc）拒绝。"""
        form = SearchForm({"start": "abc"})
        self.assertFalse(form.is_valid())
        self.assertIn("start", form.errors)

    def test_tfm06_start_after_end_rejected(self):
        """T-FM-06：start > end 拒绝（表单级校验）。"""
        form = SearchForm({"start": "2026-08-01", "end": "2026-01-01"})
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_tfm07_invalid_category_id_rejected(self):
        """T-FM-07：非法栏目 id（99999）拒绝。"""
        form = SearchForm({"category": "99999"})
        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)

    def test_tfm08_start_only_valid(self):
        """T-FM-08a：仅 start 合法。"""
        form = SearchForm({"start": "2026-01-01"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["start"].isoformat(), "2026-01-01")

    def test_tfm08b_end_only_valid(self):
        """T-FM-08b：仅 end 合法。"""
        form = SearchForm({"end": "2026-12-31"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["end"].isoformat(), "2026-12-31")

    def test_tfm08c_valid_category_id(self):
        """T-FM-08c：合法栏目 id 通过。"""
        form = SearchForm({"category": str(self.cat.pk)})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["category"], self.cat.pk)
