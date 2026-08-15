"""收紧 Django Admin 的全局访问边界。"""

from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.http import HttpRequest


class SuperuserAdminSite(AdminSite):
    """只允许活跃超级用户进入后台。"""

    def has_permission(self, request: HttpRequest) -> bool:
        """拒绝仅设置 is_staff 的不完整账户。"""
        return bool(request.user.is_active and getattr(request.user, "is_superuser", False))


class CmsAdminConfig(AdminConfig):
    """让 Django 使用收紧权限后的默认 AdminSite。"""

    default_site = "core.admin_site.SuperuserAdminSite"
