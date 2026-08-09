"""前台列表页共享的分页约定。

本模块只处理“如何分页”和“翻页链接如何保留筛选条件”，不关心被分页的
对象是文章还是其他模型，因此可以与业务查询模块保持解耦。
"""

from typing import Final

from django.core.paginator import Page, Paginator
from django.http import QueryDict

PAGE_SIZE: Final = 10


def paginate(items, page_number: int | str | None) -> Page:
    """按统一页大小返回安全页对象。

    ``Paginator.get_page()`` 会把非整数和小于 1 的页码降级为第一页，把超过
    总页数的页码降级为末页，所以视图不需要重复编写异常捕获代码。
    """
    return Paginator(items, PAGE_SIZE).get_page(page_number)


def query_without_page(query_params: QueryDict) -> str:
    """编码除 ``page`` 外的查询参数，供模板生成无重复页码的翻页链接。"""
    # request.GET 是不可变 QueryDict；复制后才能安全删除旧页码。
    query = query_params.copy()
    query.pop("page", None)
    return query.urlencode()
