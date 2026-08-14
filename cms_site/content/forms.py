"""content 应用表单定义（对应《详细设计文档》§6.1）。

SearchForm：前台查询表单（三种模式 + 组合查询的校验单元）。
- q        标题关键词（可选，≤100 字符，strip 清洗）
- start    起始日期（可选，%Y-%m-%d）
- end      结束日期（可选，%Y-%m-%d）
- category 栏目（可选，选项来自 Category 全集，动态刷新）
表单级校验：start > end 时拒绝（NFR-01 输入校验）。
"""

from datetime import timedelta

from django import forms

from .models import Category


class BrowseCategoryForm(forms.Form):
    """文章列表的栏目筛选输入边界。"""

    category = forms.ModelChoiceField(
        label="栏目",
        required=False,
        queryset=Category.objects.all(),
        empty_label="全部栏目",
    )


class SearchForm(forms.Form):
    """前台查询表单：按题目/时间/栏目三种模式组合（FR-SRCH-01~04）。"""

    q = forms.CharField(
        label="题目关键词",
        required=False,
        max_length=100,  # NFR-01：长度边界
        strip=True,  # 去除首尾空白（T-FM-02）
    )
    start = forms.DateField(
        label="起始日期",
        required=False,
        help_text="格式：YYYY-MM-DD",
        input_formats=["%Y-%m-%d"],  # 严格格式（T-FM-04/05）
        error_messages={"invalid": "日期格式应为 YYYY-MM-DD"},
    )
    end = forms.DateField(
        label="结束日期",
        required=False,
        help_text="格式：YYYY-MM-DD",
        input_formats=["%Y-%m-%d"],
        error_messages={"invalid": "日期格式应为 YYYY-MM-DD"},
    )
    category = forms.ModelChoiceField(
        label="栏目",
        required=False,
        queryset=Category.objects.all(),
        empty_label="全部栏目",
    )

    def clean_q(self):
        """关键词清洗：空字符串 → None（T-FM-01：空表单全部字段 None）。"""
        value = self.cleaned_data.get("q")
        if value in (None, ""):
            return None
        return value

    def clean(self):
        """表单级校验：起始日期不能晚于结束日期（NFR-01 示例场景）。"""
        cleaned = super().clean()
        if cleaned is None:
            return {}
        start = cleaned.get("start")
        end = cleaned.get("end")
        if start and end and start > end:
            self.add_error(
                None,
                "开始日期不能晚于结束日期",
            )
        if start and end and end - start > timedelta(days=366):
            self.add_error(None, "查询日期范围不能超过 366 天")
        return cleaned
