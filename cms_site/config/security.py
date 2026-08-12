"""按运行模式构建安全设置。"""

from __future__ import annotations

import os
from typing import TypedDict

from django.core.exceptions import ImproperlyConfigured

from . import env


class SecuritySettings(TypedDict, total=False):
    """可注入 Django settings 的安全配置。"""

    DEBUG: bool
    ALLOWED_HOSTS: list[str]
    CSRF_TRUSTED_ORIGINS: list[str]
    SESSION_COOKIE_SECURE: bool
    CSRF_COOKIE_SECURE: bool
    SECURE_PROXY_SSL_HEADER: tuple[str, str]
    SECURE_SSL_REDIRECT: bool
    SECURE_HSTS_SECONDS: int
    SECURE_HSTS_INCLUDE_SUBDOMAINS: bool
    SECURE_HSTS_PRELOAD: bool
    SILENCED_SYSTEM_CHECKS: list[str]
    SECURE_CONTENT_TYPE_NOSNIFF: bool
    SECURE_REFERRER_POLICY: str
    X_FRAME_OPTIONS: str


def build_security_settings(mode: str) -> SecuritySettings:
    """构建 Host、CSRF 与公网 HTTPS 安全配置。"""
    hosts = env.split_csv(os.environ.get("DJANGO_ALLOWED_HOSTS"))
    csrf_origins = env.split_csv(os.environ.get("CSRF_TRUSTED_ORIGINS"))
    if mode == env.MODE_PUBLIC and (not hosts or not csrf_origins):
        raise env.ConfigError("公网模式必须由 cpolar 启动器注入 Host 与 CSRF 来源")
    if not hosts:
        hosts = ["127.0.0.1", "localhost"]
    if "*" in hosts:
        raise ImproperlyConfigured("禁止使用 ALLOWED_HOSTS 通配符")

    result: SecuritySettings = {
        "ALLOWED_HOSTS": hosts,
        "CSRF_TRUSTED_ORIGINS": csrf_origins,
        "SECURE_CONTENT_TYPE_NOSNIFF": True,
        "SECURE_REFERRER_POLICY": "same-origin",
        "X_FRAME_OPTIONS": "DENY",
    }
    if mode == env.MODE_PUBLIC:
        result.update(
            {
                "DEBUG": False,
                "SESSION_COOKIE_SECURE": True,
                "CSRF_COOKIE_SECURE": True,
                "SECURE_PROXY_SSL_HEADER": ("HTTP_X_FORWARDED_PROTO", "https"),
                "SECURE_SSL_REDIRECT": True,
                "SECURE_HSTS_SECONDS": 3600,
                "SECURE_HSTS_INCLUDE_SUBDOMAINS": False,
                "SECURE_HSTS_PRELOAD": False,
                "SILENCED_SYSTEM_CHECKS": ["security.W005", "security.W021"],
            }
        )
    return result
