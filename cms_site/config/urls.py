"""
URL configuration for config project.

路由挂载（对应《详细设计文档》§7.1 路由表）：
- /            → content 应用（首页/列表/详情/搜索）
- /admin/      → Django Admin（管理端 CRUD）
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            extra_context={"page_title": "登录"},
        ),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("health/", include("core.urls")),
    path("", include("content.urls")),
]

handler400 = "core.views.handler400"
handler403 = "core.views.handler403"
handler404 = "core.views.handler404"
handler500 = "core.views.handler500"

# Admin 站点标题中文化
admin.site.site_header = "CMS 原型系统管理后台"
admin.site.site_title = "CMS 管理"
admin.site.index_title = "内容管理"
