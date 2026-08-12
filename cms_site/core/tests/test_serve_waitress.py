"""Waitress 运行配置测试。"""

from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from config.env import ConfigError, IntegerSetting, parse_int
from core.management.commands.serve_waitress import Command


class IntegerSettingTests(SimpleTestCase):
    """验证整数环境变量在配置边界完成解析。"""

    def test_returns_default_when_value_is_missing(self) -> None:
        """未配置值时使用边界对象中的默认值。"""
        setting = IntegerSetting(default=8000, minimum=1, maximum=65535)

        result = parse_int("WAITRESS_PORT", None, setting)

        self.assertEqual(result, 8000)

    def test_rejects_value_outside_range(self) -> None:
        """超出端口范围的整数被拒绝。"""
        setting = IntegerSetting(default=8000, minimum=1, maximum=65535)

        with self.assertRaises(ConfigError):
            parse_int("WAITRESS_PORT", "70000", setting)


class ServeWaitressTests(SimpleTestCase):
    """验证管理命令把运行设置传给 Waitress。"""

    @override_settings(
        WAITRESS_HOST="0.0.0.0",
        WAITRESS_PORT=8080,
        WAITRESS_THREADS=4,
        WAITRESS_TRUSTED_PROXY="127.0.0.1",
        TRUST_PROXY_HEADERS=True,
    )
    @patch("core.management.commands.serve_waitress.serve")
    def test_uses_configured_network_and_proxy_settings(self, serve) -> None:
        """容器和公网运行参数由设置注入而非硬编码。"""
        Command().handle()

        arguments = serve.call_args.kwargs
        self.assertEqual(arguments["host"], "0.0.0.0")
        self.assertEqual(arguments["port"], 8080)
        self.assertEqual(arguments["threads"], 4)
        self.assertEqual(
            arguments["trusted_proxy_headers"],
            {"x-forwarded-for", "x-forwarded-proto"},
        )
