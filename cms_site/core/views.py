"""健康检查与全局错误响应。"""

from __future__ import annotations

from django.core.cache import cache
from django.db import OperationalError, connections
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from redis.exceptions import RedisError

HEALTH_CACHE_KEY = "cms:health"
HEALTH_CACHE_VALUE = "ok"


def health_live(_request: HttpRequest) -> JsonResponse:
    """确认 Web 进程仍可响应请求。"""
    return JsonResponse({"status": "ok"})


def health_ready(_request: HttpRequest) -> JsonResponse:
    """确认数据库和缓存后端可用，且不泄露连接细节。"""
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
    except OperationalError:
        return JsonResponse({"status": "unavailable"}, status=503)

    try:
        cache.set(HEALTH_CACHE_KEY, HEALTH_CACHE_VALUE, timeout=5)
        if cache.get(HEALTH_CACHE_KEY) != HEALTH_CACHE_VALUE:
            return JsonResponse({"status": "unavailable"}, status=503)
    except (ConnectionError, RedisError):
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def handler400(request: HttpRequest, exception=None) -> HttpResponse:
    """返回不包含内部异常的 400 页面。"""
    return render(request, "400.html", status=400)


def handler403(request: HttpRequest, exception=None) -> HttpResponse:
    """返回不包含内部异常的 403 页面。"""
    return render(request, "403.html", status=403)


def handler404(request: HttpRequest, exception=None) -> HttpResponse:
    """返回不包含内部异常的 404 页面。"""
    return render(request, "404.html", status=404)


def handler500(request: HttpRequest) -> HttpResponse:
    """返回不包含堆栈信息的 500 页面。"""
    return render(request, "500.html", status=500)
