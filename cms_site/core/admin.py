"""用户角色与管理审计 Admin 注册。"""

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django.http import HttpRequest

from .admin_forms import CmsUserChangeForm, CmsUserCreationForm

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class CmsUserAdmin(UserAdmin):
    """以普通用户/管理员抽象管理 Django 用户。"""

    form = CmsUserChangeForm
    add_form = CmsUserCreationForm
    list_display = ("username", "email", "visible_role", "is_active", "last_login")
    list_filter = ("is_superuser", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("个人信息", {"fields": ("email", "first_name", "last_name")}),
        ("角色与状态", {"fields": ("role", "is_active")}),
        ("重要日期", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "role", "is_active", "password1", "password2"),
            },
        ),
    )

    @admin.display(description="角色", ordering="is_superuser")
    def visible_role(self, user: User) -> str:
        """返回后台可见的两级角色名称。"""
        return "管理员" if user.is_superuser else "普通用户"


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """只读展示 Django Admin 的管理操作审计。"""

    date_hierarchy = "action_time"
    list_display = ("action_time", "user", "action_flag", "content_type", "object_repr")
    list_filter = ("action_flag", "content_type", "action_time")
    search_fields = ("user__username", "object_repr", "change_message")
    ordering = ("-action_time",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: LogEntry | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: LogEntry | None = None) -> bool:
        return False
