"""内容管理写入边界表单。"""

from django import forms
from django.core.exceptions import ValidationError

from .models import Item


class ItemAdminForm(forms.ModelForm):
    """拒绝标题或正文只包含空白的文章。"""

    class Meta:
        model = Item
        fields = ("title", "content", "category", "author", "publish_time", "is_published")

    def clean_title(self) -> str:
        """清理并校验文章标题。"""
        title = self.cleaned_data["title"].strip()
        if not title:
            raise ValidationError("标题不能只包含空白")
        return title

    def clean_content(self) -> str:
        """清理并校验文章正文。"""
        content = self.cleaned_data["content"].strip()
        if not content:
            raise ValidationError("正文不能只包含空白")
        return content
