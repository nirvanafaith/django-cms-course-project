"""PostgreSQL 数据库设置测试。"""

import os
from unittest.mock import patch

from django.test import SimpleTestCase

from config.backends import build_databases
from config.env import ConfigError


class PostgreSQLSettingsTests(SimpleTestCase):
    """验证唯一数据库后端及凭据边界。"""

    def test_builds_only_postgresql_backend(self) -> None:
        """完整配置只生成 PostgreSQL 默认连接。"""
        values = {
            "POSTGRES_DB": "cms",
            "POSTGRES_USER": "cms_user",
            "POSTGRES_PASSWORD": "secret",
            "POSTGRES_HOST": "db",
            "POSTGRES_PORT": "5432",
        }

        with patch.dict(os.environ, values, clear=True):
            database = build_databases("local")["default"]

        self.assertEqual(database["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(database["NAME"], "cms")
        self.assertEqual(database["PORT"], "5432")
        self.assertEqual(database["CONN_MAX_AGE"], 60)
        self.assertTrue(database["CONN_HEALTH_CHECKS"])
        self.assertEqual(database["OPTIONS"], {"connect_timeout": 5})

    def test_requires_postgresql_password(self) -> None:
        """缺少密码时配置构建必须立即失败。"""
        values = {
            "POSTGRES_DB": "cms",
            "POSTGRES_USER": "cms_user",
            "POSTGRES_HOST": "db",
            "POSTGRES_PORT": "5432",
        }

        with (
            patch.dict(os.environ, values, clear=True),
            self.assertRaises(ConfigError),
        ):
            _ = build_databases("local")
