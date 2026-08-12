"""公网启动环境测试。"""

from django.test import SimpleTestCase

from core.public_runner import build_public_environment


class PublicEnvironmentTests(SimpleTestCase):
    """验证公网启动器显式声明受信任代理边界。"""

    def test_enables_proxy_headers_for_owned_cpolar_process(self) -> None:
        """应用创建的 cpolar 链路允许读取清理后的转发头。"""
        environment = build_public_environment({}, "example.cpolar.top")

        self.assertEqual(environment["TRUST_PROXY_HEADERS"], "1")
