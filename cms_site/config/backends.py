"""数据库与缓存设置构建函数。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

from django.core.exceptions import ImproperlyConfigured

from . import env


class BackendSettings(TypedDict):
    """Django 后端别名映射。"""

    default: dict[str, str | int | bool | Path | dict[str, str | int | bool]]


def build_databases(mode: str) -> BackendSettings:
    """构建数据库设置；正式运行默认 MySQL。"""
    engine = os.environ.get("DB_ENGINE")
    if engine is None:
        engine = "sqlite" if env.is_test_mode() else "mysql"

    if engine == "sqlite":
        if mode == env.MODE_PUBLIC:
            raise ImproperlyConfigured("公网模式禁止使用 SQLite，请配置 MySQL")
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": Path(os.environ.get("DB_NAME", "db.sqlite3")),
            }
        }

    if engine != "mysql":
        raise ImproperlyConfigured("DB_ENGINE 仅支持 mysql 或 sqlite")

    import pymysql

    pymysql.install_as_MySQLdb()
    return {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env.require_env("DB_NAME"),
            "USER": env.require_env("DB_USER"),
            "PASSWORD": env.require_env("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "charset": "utf8mb4",
                "connect_timeout": 5,
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
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
