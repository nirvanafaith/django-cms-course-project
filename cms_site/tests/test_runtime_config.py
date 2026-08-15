"""PostgreSQL 容器运行文件合同测试。"""

import os
from pathlib import Path

from django.test import SimpleTestCase

ROOT = (
    Path(os.environ["CMS_PROJECT_ROOT"])
    if "CMS_PROJECT_ROOT" in os.environ
    else Path(__file__).resolve().parents[2]
)


class RuntimeConfigTests(SimpleTestCase):
    """验证标准运行入口只声明 PostgreSQL。"""

    def test_compose_uses_postgresql_18_only(self) -> None:
        """Compose 固定 PostgreSQL 18.6 且不保留旧后端变量。"""
        text = (ROOT / "compose.yaml").read_text(encoding="utf-8")

        self.assertIn("postgres:18.6-bookworm", text)
        self.assertIn("POSTGRES_DB", text)
        self.assertNotIn("mysql", text.casefold())
        self.assertNotIn("DB_ENGINE", text)

    def test_requirements_remove_mysql_driver(self) -> None:
        """Python 依赖只保留 PostgreSQL 驱动。"""
        text = (ROOT / "cms_site" / "requirements.txt").read_text(encoding="utf-8")

        self.assertNotIn("PyMySQL", text)
        self.assertIn("psycopg[binary]==3.3.4", text)

    def test_dockerfile_collectstatic_uses_postgresql_variables(self) -> None:
        """镜像构建阶段不重新引入 SQLite。"""
        text = (ROOT / "cms_site" / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("POSTGRES_DB", text)
        self.assertNotIn("DB_ENGINE=sqlite", text)

    def test_launchers_use_compose_and_postgresql_variables(self) -> None:
        """本地入口委托 Compose 后台编排并校验配置，公网入口使用统一变量名。"""
        local = (ROOT / "启动系统.bat").read_text(encoding="utf-8")
        public = (ROOT / "启动公网系统.bat").read_text(encoding="utf-8")

        self.assertIn("docker compose config --quiet", local)
        self.assertIn("docker compose up -d --build --wait --remove-orphans web", local)
        self.assertIn("POSTGRES_DB", public)
        self.assertNotIn("DB_NAME", public)
