"""公共分页辅助函数的单元测试。"""

from django.http import QueryDict
from django.test import SimpleTestCase

from content.pagination import PAGE_SIZE, paginate, query_without_page


class PaginationHelperTests(SimpleTestCase):
    """验证分页约定与翻页查询字符串的构造规则。"""

    def test_paginate_uses_ten_items_per_page(self):
        """When 请求第二页，Then 每页十条并返回第 11 至 20 项。"""
        page = paginate(list(range(25)), 2)

        self.assertEqual(PAGE_SIZE, 10)
        self.assertEqual(list(page.object_list), list(range(10, 20)))

    def test_paginate_falls_back_for_non_integer_page(self):
        """When 页码不是整数，Then Django 自动回退到第一页。"""
        page = paginate(list(range(25)), "abc")

        self.assertEqual(page.number, 1)

    def test_paginate_falls_back_for_out_of_range_page(self):
        """When 页码超过总页数，Then Django 自动回退到末页。"""
        page = paginate(list(range(25)), 99)

        self.assertEqual(page.number, 3)

    def test_query_without_page_preserves_other_values(self):
        """When 构造翻页参数，Then 仅删除旧页码并保留筛选条件。"""
        query = QueryDict("q=Python&category=2&page=3")

        self.assertEqual(query_without_page(query), "q=Python&category=2")
