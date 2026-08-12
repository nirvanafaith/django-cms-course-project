"""建立 cpolar 随机 HTTPS 隧道并监督 Waitress。"""

from __future__ import annotations

import os
import sys
import webbrowser

from django.core.management.base import BaseCommand, CommandError

from core.cpolar import TunnelAddressError
from core.public_runner import PublicRunner, default_cpolar_executable


class Command(BaseCommand):
    """启动一次性公网演示会话。"""

    help = "通过 cpolar 随机 HTTPS 域名启动公网 Waitress 服务"

    def handle(self, *args, **options) -> None:
        runner = PublicRunner(default_cpolar_executable(), sys.executable)

        def announce(url: str) -> None:
            self.stdout.write(self.style.SUCCESS(f"公网地址：{url}"))
            webbrowser.open(url)

        try:
            exit_code = runner.run(os.environ, prepare=True, on_ready=announce)
        except (FileNotFoundError, PermissionError) as error:
            raise CommandError("未找到或无法执行 cpolar，请检查 CPOLAR_EXE") from error
        except TunnelAddressError as error:
            raise CommandError(str(error)) from error
        if exit_code != 0:
            raise CommandError(f"Waitress 异常退出，代码 {exit_code}")
