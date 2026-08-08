"""content 应用视图（对应《详细设计文档》§7.2 伪代码实现）。

视图：
- index       首页：栏目导航（带文章数）+ 最新 8 篇已发布文章
- item_list   栏目文章列表（可选 category 参数筛选，分页）
- item_detail 文章详情（草稿对普通用户视同 404）
- search      三种查询模式 + 组合查询（分页，参数回显）

技术要点（《技术报告》§5）：
- 时间范围/栏目过滤走索引（publish_time db_index、外键索引）
- select_related 消除列表页 N+1
- Paginator.get_page() 内建分页守卫（PageNotAnInteger → 第 1 页；EmptyPage → 末页）
- 表单校验失败 → 空结果 + 错误回显（不 500）
"""

from datetime import datetime, time as dtime, timedelta

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .forms import SearchForm
from .models import Category, Item

# 列表/搜索页每页条数（FR-PAGE-01）
PAGE_SIZE = 10


def _published_items():
    """已发布文章基础查询集（草稿对普通用户不可见，FR-ART-05）。"""
    return Item.objects.filter(is_published=True)


def index(request):
    """首页：栏目导航（含文章计数）+ 最新文章（FR-UI-01）。"""
    categories = Category.objects.annotate(item_count=Count("items"))
    latest_items = _published_items().select_related("category")[:8]
    context = {
        "categories": categories,
        "latest_items": latest_items,
        "page_title": "首页",
    }
    return render(request, "content/index.html", context)


def _request_query(request):
    """分页链接保留的查询参数（排除 page 本身，避免 ?page=1&page=2 重复，T-IT-16）。"""
    query = request.GET.copy()
    query.pop("page", None)
    return query.urlencode()


def _aware_midnight(day):
    """将 date 边界转为 aware 的当天 00:00（避免 naive datetime 警告，仍走索引）。"""
    return timezone.make_aware(datetime.combine(day, dtime.min))


def item_list(request):
    """栏目文章列表：可选 category 参数筛选（T-IT-02），分页（FR-UI-02）。"""
    qs = _published_items().select_related("category")
    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)  # 走外键索引
    page_obj = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    context = {
        "page_obj": page_obj,
        "page_title": "文章列表",
        "request_query": _request_query(request),  # 分页链接保留参数（T-IT-16）
    }
    return render(request, "content/item_list.html", context)


def item_detail(request, pk):
    """文章详情：已发布才可见，草稿视同 404（FR-UI-03 / T-IT-04/05）。"""
    item = get_object_or_404(_published_items().select_related("category"), pk=pk)
    context = {"item": item, "page_title": item.title}
    return render(request, "content/item_detail.html", context)


def search(request):
    """三种查询模式 + 组合查询（FR-SRCH-01~04 / T-IT-06~16）。

    查询逻辑（设计 §7.2）：
    - q         → title__icontains（模式 1，参数化防注入）
    - start/end → publish_time__range/gte/lte（模式 2，走索引）
    - category  → category_id 精确匹配（模式 3）
    - 各条件通过 filter 逐个叠加，实现 AND 组合
    校验失败：qs = none()（不查库、不崩溃），错误信息随表单回显。
    """
    form = SearchForm(request.GET)
    if form.is_valid():
        qs = _published_items().select_related("category")
        cleaned = form.cleaned_data
        if cleaned.get("q"):
            qs = qs.filter(title__icontains=cleaned["q"])  # 参数化，防 SQL 注入
        if cleaned.get("start"):
            # date → aware 当天 00:00（避免 naive datetime 警告，仍走索引）
            qs = qs.filter(publish_time__gte=_aware_midnight(cleaned["start"]))
        if cleaned.get("end"):
            # Django 将 lte=date 按当天 00:00 转换，会漏掉 end 当天记录；
            # 改用 end+1 天作开区间上界（保持走 publish_time 索引，见《技术报告》§5.1-3）
            qs = qs.filter(publish_time__lt=_aware_midnight(cleaned["end"] + timedelta(days=1)))
        if cleaned.get("category"):
            qs = qs.filter(category_id=cleaned["category"])
    else:
        qs = Item.objects.none()  # 校验失败不查库（T-IT-12：非法日期不 500）

    page_obj = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    context = {
        "form": form,
        "page_obj": page_obj,
        "page_title": "搜索",
        "request_query": _request_query(request),  # 分页链接保留条件（T-IT-16）
    }
    return render(request, "content/item_list.html", context)
