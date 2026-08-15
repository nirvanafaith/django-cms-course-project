"""请求关联标识和公开页面限流中间件。"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from redis.exceptions import RedisError

from .json_logging import mask_ip
from .logcontext import clear_request_id, set_request_id
from .throttling import LoginThrottle, RateLimiter

request_logger = logging.getLogger("cms.request")
security_logger = logging.getLogger("cms.security")


def client_ip(request: HttpRequest) -> str:
    """返回由 WSGI 服务器完成代理清理后的客户端地址。"""
    return request.META.get("REMOTE_ADDR", "unknown")


class RequestContextMiddleware:
    """为请求添加关联标识并在边界记录耗时。"""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        started = time.perf_counter()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            user_id = (
                request.user.pk
                if response.status_code < 500
                and hasattr(request, "user")
                and request.user.is_authenticated
                else None
            )
            request_logger.info(
                "request.complete",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    "user_id": user_id,
                    "masked_ip": mask_ip(client_ip(request)),
                },
            )
            return response
        finally:
            clear_request_id()


class PublicRateLimitMiddleware:
    """限制公开 GET 请求；后端故障时公开读取继续服务。"""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.limiter = RateLimiter()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method != "GET" or request.path.startswith(("/admin/", "/health/")):
            return self.get_response(request)

        key = f"{client_ip(request)}:{request.path}"
        try:
            result = self.limiter.hit(
                key,
                limit=settings.PUBLIC_RATE_LIMIT,
                window=settings.PUBLIC_RATE_WINDOW,
            )
        except (ConnectionError, RedisError):
            security_logger.warning(
                "rate_limit.degraded",
                extra={"path": request.path, "masked_ip": mask_ip(client_ip(request))},
            )
            return self.get_response(request)

        if result.allowed:
            return self.get_response(request)
        response = render(
            request,
            "429.html",
            {"retry_after": result.retry_after},
            status=429,
        )
        response["Retry-After"] = str(result.retry_after)
        return response


class AdminLoginThrottleMiddleware:
    """保护 Admin 登录入口，公网限流后端故障时失败关闭。"""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.throttle = LoginThrottle(
            limit=settings.ADMIN_LOGIN_FAILURE_LIMIT,
            window=settings.ADMIN_LOGIN_FAILURE_WINDOW,
            block_seconds=settings.ADMIN_LOGIN_BLOCK_SECONDS,
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path not in {"/accounts/login/", "/admin/login/"} or request.method != "POST":
            return self.get_response(request)

        username = request.POST.get("username", "")
        remote_address = client_ip(request)
        try:
            result = self.throttle.check(username, remote_address)
        except (ConnectionError, RedisError):
            security_logger.warning(
                "login_throttle.degraded",
                extra={"path": request.path, "masked_ip": mask_ip(remote_address)},
            )
            if settings.DJANGO_MODE == "public":
                return HttpResponse("Service unavailable", status=503)
            return self.get_response(request)

        if not result.allowed:
            security_logger.warning(
                "login.blocked",
                extra={"path": request.path, "masked_ip": mask_ip(remote_address)},
            )
            response = render(
                request,
                "429.html",
                {"retry_after": result.retry_after},
                status=429,
            )
            response["Retry-After"] = str(result.retry_after)
            return response

        response = self.get_response(request)
        try:
            if 300 <= response.status_code < 400:
                self.throttle.clear(username, remote_address)
            elif response.status_code == 200:
                self.throttle.record_failure(username, remote_address)
                security_logger.warning(
                    "login.failed",
                    extra={"path": request.path, "masked_ip": mask_ip(remote_address)},
                )
        except (ConnectionError, RedisError):
            security_logger.warning(
                "login_throttle.degraded",
                extra={"path": request.path, "masked_ip": mask_ip(remote_address)},
            )
        return response
