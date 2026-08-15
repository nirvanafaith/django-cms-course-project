"""内容业务应用的 Django 注册信息。"""

from django.apps import AppConfig


class ContentConfig(AppConfig):
    """告诉 Django 如何发现 content 应用及其模型、Admin 和命令。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "content"
    verbose_name = "内容管理"
