"""cpolar 公网 HTTPS 地址解析合同测试。"""

from django.test import SimpleTestCase

from core.cpolar import PublicTunnel, TunnelAddressError, extract_https_tunnel


class ExtractHttpsTunnelTests(SimpleTestCase):
    """验证真实 cpolar 日志格式下只提取唯一且安全的 HTTPS 地址。"""

    def test_extracts_url_quoted_inside_log_message(self) -> None:
        """cpolar 3.x 把地址放在 msg=\"...\" 引号内，不能把尾引号吞进 URL。"""
        log = (
            'time="2026-08-15T14:22:46+08:00" level=info '
            'msg="[:tunnel server module] Tunnel established at '
            'https://452a2eeb.r7.cpolar.top"'
        )

        tunnel = extract_https_tunnel(log)

        self.assertEqual(
            tunnel,
            PublicTunnel(url="https://452a2eeb.r7.cpolar.top", host="452a2eeb.r7.cpolar.top"),
        )

    def test_extracts_plain_unquoted_url(self) -> None:
        """早期或简化的日志中裸 URL 仍可解析。"""
        tunnel = extract_https_tunnel("Tunnel established at https://demo.cpolar.cn")

        self.assertEqual(tunnel, PublicTunnel(url="https://demo.cpolar.cn", host="demo.cpolar.cn"))

    def test_rejects_missing_https_address(self) -> None:
        """只有 HTTP 地址或没有地址时按失败处理，绝不暴露非 HTTPS 入口。"""
        for log in (
            "Tunnel established at http://demo.cpolar.top",
            "authenticated with switch server",
        ):
            with self.subTest(log=log), self.assertRaises(TunnelAddressError):
                extract_https_tunnel(log)

    def test_rejects_ambiguous_addresses(self) -> None:
        """同一日志中出现多个合法地址时拒绝，避免随机选择不安全域名。"""
        log = 'first https://a.cpolar.top second msg="Tunnel established at https://b.cpolar.top"'

        with self.assertRaises(TunnelAddressError):
            extract_https_tunnel(log)
