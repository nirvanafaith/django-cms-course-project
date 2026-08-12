"""公开内容缓存失效测试。"""

from unittest.mock import patch

from django.test import SimpleTestCase

from core.caching import home_cache_key, invalidate_items, item_cache_key


class CacheInvalidationTests(SimpleTestCase):
    """验证批量写操作只产生一次缓存后端删除。"""

    @patch("core.caching.cache.delete_many")
    def test_invalidates_items_and_home_in_one_operation(self, delete_many) -> None:
        """多个文章键与首页键通过同一批量调用失效。"""
        invalidate_items((3, 5, 8))

        delete_many.assert_called_once_with(
            [item_cache_key(3), item_cache_key(5), item_cache_key(8), home_cache_key()]
        )
