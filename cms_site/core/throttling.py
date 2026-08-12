"""基于 Django 缓存后端的固定窗口限流。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from django.core.cache import cache


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    """一次限流判断结果。"""

    allowed: bool
    retry_after: int


class RateLimiter:
    """使用缓存原子 add/incr 实现固定窗口计数。"""

    def hit(self, key: str, *, limit: int, window: int) -> RateLimitResult:
        """记录一次访问并返回是否允许。"""
        cache_key = f"cms:rate:{key}"
        count = 1 if cache.add(cache_key, 1, timeout=window) else cache.incr(cache_key)
        if count <= limit:
            return RateLimitResult(allowed=True, retry_after=0)
        return RateLimitResult(allowed=False, retry_after=window)


class LoginThrottle:
    """按用户名摘要和客户端 IP 限制登录失败。"""

    def __init__(self, *, limit: int, window: int, block_seconds: int) -> None:
        self.limit = limit
        self.window = window
        self.block_seconds = block_seconds

    def _key(self, username: str, client_ip: str) -> str:
        normalized = username.strip().casefold().encode()
        digest = hashlib.sha256(normalized).hexdigest()
        return f"cms:throttle:admin:{client_ip}:{digest}"

    def check(self, username: str, client_ip: str) -> RateLimitResult:
        """返回当前登录组合是否处于封禁状态。"""
        blocked = cache.get(f"{self._key(username, client_ip)}:blocked")
        if blocked:
            return RateLimitResult(allowed=False, retry_after=self.block_seconds)
        return RateLimitResult(allowed=True, retry_after=0)

    def record_failure(self, username: str, client_ip: str) -> None:
        """记录失败并在达到阈值时创建封禁键。"""
        key = self._key(username, client_ip)
        count = 1 if cache.add(key, 1, timeout=self.window) else cache.incr(key)
        if count >= self.limit:
            cache.set(f"{key}:blocked", 1, timeout=self.block_seconds)

    def clear(self, username: str, client_ip: str) -> None:
        """成功登录后清除失败和封禁状态。"""
        key = self._key(username, client_ip)
        cache.delete_many([key, f"{key}:blocked"])
