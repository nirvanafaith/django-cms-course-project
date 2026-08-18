"""Windows 启动脚本的交互行为合同。"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
LOCAL_LAUNCHER: Final = PROJECT_ROOT / "启动系统.bat"
PUBLIC_LAUNCHER: Final = PROJECT_ROOT / "启动公网系统.bat"


@unittest.skipUnless(os.name == "nt", "Windows CMD launcher tests")
class LaunchScriptTests(unittest.TestCase):
    """验证双击启动时日志、地址与错误不会被隐藏。"""

    def test_local_launcher_streams_compose_and_keeps_final_status_visible(self) -> None:
        """本地容器以前台模式运行并在退出后显示最终状态。"""
        content = LOCAL_LAUNCHER.read_text(encoding="utf-8")

        self.assertIn(
            "docker compose up --build --remove-orphans --abort-on-container-failure web",
            content,
        )
        self.assertNotIn("docker compose up -d", content)
        self.assertIn("http://127.0.0.1:8000/", content)
        self.assertIn("Press Ctrl+C to stop the local CMS containers.", content)
        self.assertIn("docker compose ps", content)
        self.assertIn("pause >nul", content)

    def test_public_launcher_keeps_output_and_error_pause(self) -> None:
        """公网服务显示启动说明、Ctrl+C 提示和收尾暂停。"""
        content = PUBLIC_LAUNCHER.read_text(encoding="utf-8")

        self.assertIn("The public URL will be printed after the HTTPS tunnel is ready.", content)
        self.assertIn("Press Ctrl+C to stop the public CMS service.", content)
        self.assertIn("Press any key to close this window.", content)
        self.assertIn("pause >nul", content)
