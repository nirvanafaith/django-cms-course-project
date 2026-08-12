"""使用有界 Waitress 线程池启动 WSGI 应用。"""

from django.conf import settings
from django.core.management.base import BaseCommand
from waitress import serve

from config.wsgi import application


class Command(BaseCommand):
    """按运行环境设置启动 Waitress 服务。"""

    help = "使用 Waitress 启动 CMS"

    def handle(self, *args, **options) -> None:
        trusted_proxy_headers = {"x-forwarded-proto"}
        if settings.TRUST_PROXY_HEADERS:
            trusted_proxy_headers.add("x-forwarded-for")

        serve(
            application,
            host=settings.WAITRESS_HOST,
            port=settings.WAITRESS_PORT,
            threads=settings.WAITRESS_THREADS,
            connection_limit=100,
            backlog=128,
            channel_timeout=60,
            max_request_header_size=16384,
            max_request_body_size=10 * 1024 * 1024,
            expose_tracebacks=False,
            trusted_proxy=settings.WAITRESS_TRUSTED_PROXY,
            trusted_proxy_count=1,
            trusted_proxy_headers=trusted_proxy_headers,
            clear_untrusted_proxy_headers=True,
        )
