"""cpolar 输出中的公网 HTTPS 地址解析。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final
from urllib.parse import urlsplit

HTTPS_URL_PATTERN: Final = re.compile(r"https://[^\s]+")
CPOLAR_SUFFIXES: Final = (".cpolar.top", ".cpolar.cn", ".cpolar.io")


class TunnelAddressError(ValueError):
    """cpolar 输出不包含唯一且安全的 HTTPS 地址。"""


@dataclass(frozen=True, slots=True)
class PublicTunnel:
    """经过边界校验的 cpolar 公网地址。"""

    url: str
    host: str


def extract_https_tunnel(log_text: str) -> PublicTunnel:
    """从日志中解析唯一、无路径的官方 cpolar HTTPS 地址。"""
    candidates = set(HTTPS_URL_PATTERN.findall(log_text))
    valid: list[PublicTunnel] = []
    for candidate in candidates:
        parsed = urlsplit(candidate)
        host = parsed.hostname or ""
        has_safe_shape = (
            parsed.scheme == "https"
            and parsed.username is None
            and parsed.password is None
            and parsed.port is None
            and parsed.path in {"", "/"}
            and not parsed.query
            and not parsed.fragment
            and any(host.endswith(suffix) for suffix in CPOLAR_SUFFIXES)
        )
        if has_safe_shape:
            valid.append(PublicTunnel(url=f"https://{host}", host=host))
    if len(valid) != 1:
        raise TunnelAddressError("未找到唯一且合法的 cpolar HTTPS 地址")
    return valid[0]
