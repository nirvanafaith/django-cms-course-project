"""
Django settings for config project.

CMS 原型系统全局配置（对应《详细设计文档》§3.2/§10/§13、《系统部署说明书》§4）。

本文件为开发默认值；生产环境通过环境变量覆盖（见下文 SECRET_KEY/DEBUG/ALLOWED_HOSTS）。
"""

import os
from pathlib import Path

from . import backends, env, security

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# 生产环境必须通过环境变量注入（NFR-02 生产配置要求）。
DJANGO_MODE = env.get_mode()
SECRET_KEY = (
    env.require_env("DJANGO_SECRET_KEY")
    if DJANGO_MODE == env.MODE_PUBLIC
    else os.environ.get(
        "DJANGO_SECRET_KEY",
        "django-insecure-2bc5otkqv&mo8ui&o&&@#sv)x+^o9tbiqqeff1%(3^b=ksxbf*",
    )
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.parse_bool(os.environ.get("DJANGO_DEBUG"), default=True)
globals().update(security.build_security_settings(DJANGO_MODE))


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.staticfiles",
    "content",  # 业务应用：栏目 Category / 文章 Item
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.RequestContextMiddleware",
    "core.middleware.PublicRateLimitMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.AdminLoginThrottleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if not env.is_test_mode():
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # 项目级模板目录（设计 §4 目录树）
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

WAITRESS_HOST = os.environ.get("WAITRESS_HOST", "127.0.0.1")
WAITRESS_PORT = env.parse_int(
    "WAITRESS_PORT",
    os.environ.get("WAITRESS_PORT"),
    env.IntegerSetting(default=8000, minimum=1, maximum=65535),
)
WAITRESS_THREADS = env.parse_int(
    "WAITRESS_THREADS",
    os.environ.get("WAITRESS_THREADS"),
    env.IntegerSetting(default=8, minimum=1, maximum=64),
)
WAITRESS_TRUSTED_PROXY = os.environ.get("WAITRESS_TRUSTED_PROXY", "127.0.0.1")


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = backends.build_databases(DJANGO_MODE)
CACHES = backends.build_caches(DJANGO_MODE)
REDIS_URL = os.environ.get("REDIS_URL", "")
THROTTLE_BACKEND = "redis" if REDIS_URL else "memory"
TRUST_PROXY_HEADERS = env.parse_bool(os.environ.get("TRUST_PROXY_HEADERS"))
PUBLIC_RATE_LIMIT = int(os.environ.get("PUBLIC_RATE_LIMIT", "6000"))
PUBLIC_RATE_WINDOW = int(os.environ.get("PUBLIC_RATE_WINDOW", "60"))
PUBLIC_PAGE_CACHE_ENABLED = not env.is_test_mode()
ADMIN_LOGIN_FAILURE_LIMIT = int(os.environ.get("ADMIN_LOGIN_FAILURE_LIMIT", "5"))
ADMIN_LOGIN_FAILURE_WINDOW = int(os.environ.get("ADMIN_LOGIN_FAILURE_WINDOW", "300"))
ADMIN_LOGIN_BLOCK_SECONDS = int(os.environ.get("ADMIN_LOGIN_BLOCK_SECONDS", "900"))


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "zh-hans"  # 中文化后台与页面（设计 §3.2）

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # 项目级静态目录（Bootstrap 本地化备选）
STATIC_ROOT = BASE_DIR / "staticfiles"  # 生产 collectstatic 输出
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if DJANGO_MODE == env.MODE_PUBLIC
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}


# 会话安全（设计 §10 安全设计表，NFR-02）

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True


# 日志（设计 §13）：统一写入标准输出，由运行环境负责采集与轮转。

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if DEBUG else "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "cms.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "cms.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
