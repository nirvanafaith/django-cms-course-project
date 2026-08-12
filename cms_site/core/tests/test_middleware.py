"""基础设施中间件的请求边界测试。"""

from django.test import RequestFactory, SimpleTestCase, override_settings

from core.middleware import client_ip


class ClientIpTests(SimpleTestCase):
    """验证客户端地址只从明确授权的请求字段读取。"""

    def setUp(self) -> None:
        """创建真实 Django 请求对象。"""
        self.factory = RequestFactory()

    @override_settings(TRUST_PROXY_HEADERS=False)
    def test_uses_remote_address_when_proxy_headers_are_untrusted(self) -> None:
        """未信任代理时忽略可由客户端伪造的转发头。"""
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="203.0.113.8",
        )

        result = client_ip(request)

        self.assertEqual(result, "10.0.0.5")

    @override_settings(TRUST_PROXY_HEADERS=True)
    def test_uses_waitress_normalized_remote_address(self) -> None:
        """业务层只读取由 Waitress 完成代理清理后的地址。"""
        request = self.factory.get(
            "/",
            REMOTE_ADDR="127.0.0.1",
            HTTP_X_FORWARDED_FOR="203.0.113.8, 127.0.0.1",
        )

        result = client_ip(request)

        self.assertEqual(result, "127.0.0.1")
