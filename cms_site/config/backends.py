"""数据库与缓存设置构建函数。"""

from __future__ import annotations

import os
from typing import TypedDict

from . import env


class BackendSettings(TypedDict):
    """Django 后端别名映射。"""

    default: dict[str, str | int | bool | dict[str, str | int | bool]]


def build_databases(_mode: str) -> BackendSettings:
    """构建唯一受支持的 PostgreSQL 数据库连接。"""
    return {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env.require_env("POSTGRES_DB"),
            "USER": env.require_env("POSTGRES_USER"),
            "PASSWORD": env.require_env("POSTGRES_PASSWORD"),
            "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {"connect_timeout": 5},
        }
    }


def build_caches(mode: str) -> BackendSettings:
    """构建缓存设置；公网模式强制 Redis。"""
    redis_url = os.environ.get("REDIS_URL")
    if mode == env.MODE_PUBLIC and not redis_url:
        raise env.ConfigError("公网模式缺少必需的配置变量：REDIS_URL")
    if redis_url:
        return {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": redis_url,
                "KEY_PREFIX": "cms:cache:v1",
                "TIMEOUT": 300,
                "OPTIONS": {
                    "socket_connect_timeout": 1,
                    "socket_timeout": 1,
                },
            }
        }
    return {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "cms-local-cache",
            "KEY_PREFIX": "cms:cache:v1",
            "TIMEOUT": 300,
        }
    }
