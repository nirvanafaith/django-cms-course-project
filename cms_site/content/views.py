"""content 应用的 HTTP 视图编排。

视图是浏览器请求与应用内部模块之间的适配层：读取请求、触发表单校验、调用
selector 和分页辅助函数、组装模板上下文，然后返回 HTTP 响应。复杂的 ORM 查询
在 ``selectors.py``，通用分页规则在 ``pagination.py``，这样每个模块只有一种
主要变化原因，也更容易在答辩中解释调用链。
"""

from typing import TypedDict

from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from core.caching import get_or_load, home_cache_key, item_cache_key

from .forms import BrowseCategoryForm, SearchForm
from .models import Category, Item
from .pagination import page_number, paginate, query_without_page
from .selectors import (
    categories_with_item_counts,
    homepage_items,
    published_item_by_pk,
    published_items_for_category,
    search_published_items,
)


class HomeContext(TypedDict):
    """首页模板所需的数据结构。"""

    categories: list[Category]
    grouped_items: dict[str, list[Item]]
    latest_items: list[Item]
    headline_items: list[Item]
    teaching_items: list[Item]
    campus_items: list[Item]
    notice_items: list[Item]
    page_title: str


def index(request: HttpRequest) -> HttpResponse:
    """渲染首页：栏目导航、最新内容和按栏目分组的有界内容。"""

    def load_home_data() -> HomeContext:
        categories = list(categories_with_item_counts())
        items = list(homepage_items())
        grouped_items: dict[str, list[Item]] = {category.name: [] for category in categories}
        for item in items:
            grouped_items[item.category.name].append(item)
        return {
            "categories": categories,
            "grouped_items": grouped_items,
            "latest_items": items,
            "headline_items": grouped_items.get("交大头条", []),
            "teaching_items": grouped_items.get("教学科研", []),
            "campus_items": grouped_items.get("校园动态", []),
            "notice_items": grouped_items.get("通知公告", []),
            "page_title": "首页",
        }

    context = (
        get_or_load(home_cache_key(), 30, load_home_data)
        if settings.PUBLIC_PAGE_CACHE_ENABLED
        else load_home_data()
    )
    return render(request, "content/index.html", context)


def item_list(request: HttpRequest) -> HttpResponse:
    """渲染文章列表，并在输入边界验证可选栏目。"""
    form = BrowseCategoryForm(request.GET)
    form_is_valid = form.is_valid()
    current_category = form.cleaned_data["category"] if form_is_valid else None
    items = published_items_for_category(current_category) if form_is_valid else Item.objects.none()

    context = {
        "form": form,
        "page_obj": paginate(items, page_number(request.GET)),
        "page_title": "文章列表",
        "request_query": query_without_page(request.GET),
        "current_category": current_category,
    }
    return render(request, "content/item_list.html", context)


def item_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """渲染已发布文章详情；草稿和不存在的主键都返回 404。"""
    try:
        item = (
            get_or_load(item_cache_key(pk), 60, lambda: published_item_by_pk(pk))
            if settings.PUBLIC_PAGE_CACHE_ENABLED
            else published_item_by_pk(pk)
        )
    except Item.DoesNotExist as error:
        # 对普通访问者隐藏草稿是否存在，和不存在的文章使用相同 HTTP 结果。
        raise Http404("文章不存在或尚未发布") from error

    return render(
        request,
        "content/item_detail.html",
        {"item": item, "page_title": item.title},
    )


def search(request: HttpRequest) -> HttpResponse:
    """校验搜索条件、调用组合查询并渲染带分页的结果列表。"""
    form = SearchForm(request.GET)
    current_category = None
    if form.is_valid():
        cleaned = form.cleaned_data
        current_category = cleaned["category"]
        items = search_published_items(
            keyword=cleaned["q"],
            start=cleaned["start"],
            end=cleaned["end"],
            category=current_category,
        )
    else:
        # 表单是输入边界；校验失败时不查询数据库，只回显错误信息。
        items = Item.objects.none()

    context = {
        "form": form,
        "page_obj": paginate(items, page_number(request.GET)),
        "page_title": "文章查询",
        "request_query": query_without_page(request.GET),
        "current_category": current_category,
    }
    return render(request, "content/item_list.html", context)
