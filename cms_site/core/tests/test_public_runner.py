"""公网启动环境与子进程契约测试。"""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from core.cpolar import PublicTunnel
from core.public_runner import PublicRunner, build_public_environment


class PublicEnvironmentTests(SimpleTestCase):
    """验证公网启动器显式声明受信任代理边界。"""

    def test_enables_proxy_headers_for_owned_cpolar_process(self) -> None:
        """应用创建的 cpolar 链路允许读取清理后的转发头。"""
        environment = build_public_environment({}, "example.cpolar.top")

        self.assertEqual(environment["TRUST_PROXY_HEADERS"], "1")

    @patch("core.public_runner.wait_for_tunnel")
    @patch("core.public_runner.subprocess.Popen")
    def test_starts_waitress_in_text_mode(
        self,
        popen: MagicMock,
        wait_for_tunnel: MagicMock,
    ) -> None:
        """Waitress 进程继承文本子进程合同，便于一致地监督生命周期。"""
        tunnel_process = MagicMock()
        server_process = MagicMock()
        server_process.wait.return_value = 0
        popen.side_effect = (tunnel_process, server_process)
        wait_for_tunnel.return_value = PublicTunnel(
            url="https://example.cpolar.top",
            host="example.cpolar.top",
        )

        exit_code = PublicRunner("cpolar", "python").run({})

        self.assertEqual(exit_code, 0)
        self.assertTrue(popen.call_args_list[1].kwargs["text"])
