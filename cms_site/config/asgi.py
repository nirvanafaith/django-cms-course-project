"""ASGI 异步服务器入口。

ASGI 是现代 Python Web 服务器与 Django 之间的异步接口标准。本项目主要使用
同步 Django 视图，但保留该入口，便于部署到支持 ASGI 的服务器。

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
