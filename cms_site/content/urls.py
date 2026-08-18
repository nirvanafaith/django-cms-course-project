"""
content 应用路由表（对应《详细设计文档》§7.1）。

路由模式            视图函数         参数                 功能
/                   index           —                    首页：栏目导航 + 最新文章
/item/<int:pk>/     item_detail     pk                   文章详情
/search/            search          q/start/end/category  三种查询模式 + 组合（分页）
"""

from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("", views.index, name="index"),
    path("item/<int:pk>/", views.item_detail, name="item_detail"),
    path("search/", views.search, name="search"),
]
