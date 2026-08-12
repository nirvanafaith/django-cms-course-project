"""跨业务应用能力的 Django 配置。"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """注册健康检查、安全与缓存基础设施。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self) -> None:
        """注册内容缓存失效信号。"""
        from . import signals  # noqa: F401
