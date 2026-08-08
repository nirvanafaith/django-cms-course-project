"""
URL configuration for config project.

路由挂载（对应《详细设计文档》§7.1 路由表）：
- /            → content 应用（首页/列表/详情/搜索）
- /admin/      → Django Admin（管理端 CRUD）
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("content.urls")),
]

# Admin 站点标题中文化
admin.site.site_header = "CMS 原型系统管理后台"
admin.site.site_title = "CMS 管理"
admin.site.index_title = "内容管理"
