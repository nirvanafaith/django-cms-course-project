"""WSGI 同步服务器入口。

WSGI 是传统 Python Web 服务器与 Django 之间的接口标准。Waitress、Gunicorn
等部署工具会导入这里的 ``application``，而不是重新执行每个视图文件。

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
