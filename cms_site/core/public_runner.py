"""公网启动所需的子环境与进程所有权工具。"""

from __future__ import annotations

import os
import queue
import subprocess
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Final, TextIO

from .cpolar import PublicTunnel, TunnelAddressError, extract_https_tunnel

TUNNEL_TIMEOUT_SECONDS: Final = 30


def build_public_environment(source: Mapping[str, str], host: str) -> dict[str, str]:
    """复制环境并注入本次随机域名，不修改父进程环境。"""
    result = dict(source)
    result.update(
        {
            "DJANGO_MODE": "public",
            "DJANGO_DEBUG": "0",
            "DJANGO_ALLOWED_HOSTS": f"127.0.0.1,localhost,{host}",
            "CSRF_TRUSTED_ORIGINS": f"https://{host}",
            "TRUST_PROXY_HEADERS": "1",
        }
    )
    return result


def stop_owned_process(process: subprocess.Popen[str] | None) -> None:
    """仅终止调用方保存的子进程对象。"""
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def wait_for_tunnel(
    process: subprocess.Popen[str],
    *,
    timeout: int = TUNNEL_TIMEOUT_SECONDS,
) -> PublicTunnel:
    """读取 cpolar 日志直到出现合法 HTTPS 地址或进程失败。"""
    output: TextIO | None = process.stdout
    if output is None:
        raise TunnelAddressError("cpolar 未提供可读取的日志输出")

    deadline = time.monotonic() + timeout
    lines: list[str] = []
    line_queue: queue.Queue[str] = queue.Queue()

    def read_line() -> None:
        line_queue.put(output.readline())

    while time.monotonic() < deadline:
        reader = threading.Thread(target=read_line, daemon=True)
        reader.start()
        remaining = max(0.0, deadline - time.monotonic())
        try:
            line = line_queue.get(timeout=remaining)
        except queue.Empty:
            break
        if line:
            lines.append(line)
            try:
                return extract_https_tunnel("".join(lines))
            except TunnelAddressError:
                continue
        if process.poll() is not None:
            break
    raise TunnelAddressError("cpolar 未在限定时间内建立 HTTPS 隧道")


class PublicRunner:
    """监督本次 cpolar 与 Waitress 子进程的生命周期。"""

    def __init__(self, cpolar_executable: str, python_executable: str) -> None:
        self.cpolar_executable = cpolar_executable
        self.python_executable = python_executable

    def _prepare(self, environment: Mapping[str, str]) -> None:
        """在公网子环境中执行部署硬门槛。"""
        commands = (
            ("manage.py", "check", "--deploy"),
            ("manage.py", "migrate", "--noinput"),
            ("manage.py", "seed_data"),
            ("manage.py", "collectstatic", "--noinput"),
            ("manage.py", "preflight", "--mode", "public"),
        )
        for arguments in commands:
            subprocess.run(
                [self.python_executable, *arguments],
                env=dict(environment),
                check=True,
            )

    def run(
        self,
        source_environment: Mapping[str, str],
        *,
        prepare: bool = False,
        on_ready: Callable[[str], None] | None = None,
    ) -> int:
        """建立隧道，注入随机域名并运行 Waitress。"""
        tunnel_process: subprocess.Popen[str] | None = None
        server_process: subprocess.Popen[str] | None = None
        try:
            tunnel_process = subprocess.Popen(
                [
                    self.cpolar_executable,
                    "http",
                    "-log=stdout",
                    "-log-level=INFO",
                    "8000",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            tunnel = wait_for_tunnel(tunnel_process)
            environment = build_public_environment(source_environment, tunnel.host)
            if prepare:
                self._prepare(environment)
            if on_ready is not None:
                on_ready(tunnel.url)
            server_process = subprocess.Popen(
                [self.python_executable, "manage.py", "serve_waitress"],
                env=environment,
            )
            return server_process.wait()
        finally:
            stop_owned_process(server_process)
            stop_owned_process(tunnel_process)


def default_cpolar_executable() -> str:
    """返回环境覆盖值或 Windows 默认 cpolar 路径。"""
    return os.environ.get("CPOLAR_EXE", str(Path("C:/Program Files/cpolar/cpolar.exe")))
