"""内置用户模型的两级角色 Admin 表单。"""

from typing import Final

from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import User

ROLE_NORMAL: Final = "normal"
ROLE_ADMIN: Final = "admin"
ROLE_CHOICES: Final = ((ROLE_NORMAL, "普通用户"), (ROLE_ADMIN, "管理员"))


def apply_role(user: User, role: str) -> User:
    """将已清洗的角色同步到 staff 与 superuser。"""
    is_admin = role == ROLE_ADMIN
    user.is_staff = is_admin
    user.is_superuser = is_admin
    return user


class CmsUserCreationForm(UserCreationForm):
    """创建普通用户或管理员并使用 Django 密码校验。"""

    email = forms.EmailField(label="电子邮箱", required=False)
    is_active = forms.BooleanField(label="启用", required=False, initial=True)
    role = forms.ChoiceField(label="角色", choices=ROLE_CHOICES)

    def save(self, commit: bool = True) -> User:
        """保存用户并同步角色标志。"""
        user = apply_role(super().save(commit=False), self.cleaned_data["role"])
        user.email = self.cleaned_data["email"]
        user.is_active = self.cleaned_data["is_active"]
        if commit:
            user.save()
        return user


class CmsUserChangeForm(UserChangeForm):
    """修改用户资料、状态和两级角色。"""

    role = forms.ChoiceField(label="角色", choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "is_active",
            "role",
        )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["role"].initial = ROLE_ADMIN if self.instance.is_superuser else ROLE_NORMAL

    def save(self, commit: bool = True) -> User:
        """保存用户并同步角色标志。"""
        user = apply_role(super().save(commit=False), self.cleaned_data["role"])
        if commit:
            user.save()
        return user
