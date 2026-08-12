"""公开内容的版本化缓存接口。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from django.core.cache import cache
from redis.exceptions import RedisError

CACHE_PREFIX: Final = "cms:page:v1"


def home_cache_key() -> str:
    """返回首页数据缓存键。"""
    return f"{CACHE_PREFIX}:home"


def item_cache_key(pk: int) -> str:
    """返回公开文章详情缓存键。"""
    return f"{CACHE_PREFIX}:item:{pk}"


def get_or_load[T](key: str, timeout: int, loader: Callable[[], T]) -> T:
    """读取缓存；缓存故障或未命中时执行加载器。"""
    try:
        value = cache.get(key)
    except (ConnectionError, RedisError):
        return loader()
    if value is not None:
        return value

    value = loader()
    try:
        cache.set(key, value, timeout=timeout)
    except (ConnectionError, RedisError):
        return value
    return value


def invalidate_home() -> None:
    """失效首页公开数据。"""
    try:
        cache.delete(home_cache_key())
    except (ConnectionError, RedisError):
        return


def invalidate_item(pk: int) -> None:
    """失效文章详情及首页数据。"""
    try:
        cache.delete_many([item_cache_key(pk), home_cache_key()])
    except (ConnectionError, RedisError):
        return


def invalidate_items(primary_keys: tuple[int, ...]) -> None:
    """通过一次后端操作失效一组文章详情及首页数据。"""
    keys = [item_cache_key(primary_key) for primary_key in primary_keys]
    keys.append(home_cache_key())
    try:
        cache.delete_many(keys)
    except (ConnectionError, RedisError):
        return
