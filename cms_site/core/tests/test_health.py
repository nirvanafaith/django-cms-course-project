"""基础设施健康检查测试。"""

from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse


class HealthReadyTests(TestCase):
    """验证就绪端点检查缓存写读闭环。"""

    @patch("core.views.cache.get", return_value=None)
    @patch("core.views.cache.set")
    def test_returns_unavailable_when_cache_readback_differs(self, _set, _get) -> None:
        """缓存没有读回探针值时不能声明服务就绪。"""
        response = self.client.get(reverse("health_ready"))

        self.assertEqual(response.status_code, 503)

    @patch("core.views.cache.get", return_value="ok")
    @patch("core.views.cache.set")
    def test_returns_ok_when_dependencies_are_ready(self, _set, _get) -> None:
        """数据库和缓存探针成功时返回 200。"""
        response = self.client.get(reverse("health_ready"))

        self.assertEqual(response.status_code, 200)


class PreflightTests(TestCase):
    """验证启动前检查拒绝无法正确读回的缓存。"""

    @patch("core.management.commands.preflight.cache.get", return_value=None)
    @patch("core.management.commands.preflight.cache.set")
    def test_rejects_cache_readback_mismatch(self, _set, _get) -> None:
        """缓存探针读回不一致时启动检查必须失败。"""
        with self.assertRaises(CommandError):
            call_command("preflight", mode="local")
