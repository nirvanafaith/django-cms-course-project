"""content 应用视图。

本项目骨架阶段（commit 2）先提供最小占位实现，保证 URLconf 可解析、项目可启动；
完整业务逻辑在后续提交中实现（对应《技术报告》§8.1 提交序列）：
- commit 5：前台视图与路由（index/item_list/item_detail/search 完整实现）
- commit 7：模板渲染
"""

from django.http import HttpResponse


def index(request):
    """首页占位：栏目导航 + 最新文章（完整实现见 commit 5）。"""
    return HttpResponse("CMS 首页（占位）")


def item_list(request):
    """栏目文章列表占位（完整实现见 commit 5）。"""
    return HttpResponse("栏目文章列表（占位）")


def item_detail(request, pk):
    """文章详情占位（完整实现见 commit 5）。"""
    return HttpResponse(f"文章详情（占位）pk={pk}")


def search(request):
    """三种查询模式搜索页占位（完整实现见 commit 5）。"""
    return HttpResponse("搜索页（占位）")
