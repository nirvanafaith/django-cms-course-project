"""前台页面使用的只读数据库查询。

Selector（查询器）只负责使用 Django ORM 读取数据，不读取 ``HttpRequest``，
也不决定模板、分页或 HTTP 状态码。视图只需传入已经过表单校验的 Python 值，
因此查询规则可以脱离浏览器请求进行独立测试和复用。
"""

from datetime import date, datetime, time, timedelta

from django.db.models import QuerySet
from django.utils import timezone

from .models import Category, Item


def _aware_midnight(day: date) -> datetime:
    """把一个日期转换为当前时区当天 00:00 的时区感知时间。"""
    naive_midnight = datetime.combine(day, time.min)
    return timezone.make_aware(naive_midnight)


def homepage_items(limit: int = 24) -> QuerySet[Item]:
    """返回首页所需的有界已发布文章，预加载模板读取的外键。"""
    return (
        Item.objects.filter(is_published=True)
        .select_related("category", "author")
        .order_by("-publish_time", "-pk")[:limit]
    )


def published_item_by_pk(pk: int) -> Item:
    """按主键返回一篇已发布文章；不存在或为草稿时抛出 ``DoesNotExist``。"""
    return (
        Item.objects.filter(is_published=True)
        .select_related("category", "author")
        .order_by("-publish_time", "-pk")
        .get(pk=pk)
    )


def search_published_items(
    *,
    keyword: str | None = None,
    start: date | None = None,
    end: date | None = None,
    category: Category | None = None,
) -> QuerySet[Item]:
    """根据已校验的可选条件，以 AND 语义组合已发布文章查询。"""
    queryset = (
        Item.objects.filter(is_published=True)
        .select_related("category", "author")
        .order_by("-publish_time", "-pk")
    )
    if keyword:
        queryset = queryset.filter(title__icontains=keyword)
    if start:
        queryset = queryset.filter(publish_time__gte=_aware_midnight(start))
    if end:
        # 使用“下一天零点之前”的开区间，才能包含结束日期当天的全部时刻。
        end_exclusive = _aware_midnight(end + timedelta(days=1))
        queryset = queryset.filter(publish_time__lt=end_exclusive)
    if category:
        queryset = queryset.filter(category=category)
    return queryset
