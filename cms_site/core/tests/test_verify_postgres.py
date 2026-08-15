"""PostgreSQL 服务端版本验证命令测试。"""

from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class VerifyPostgresTests(SimpleTestCase):
    """验证运行时拒绝错误数据库类型或版本。"""

    @patch("core.management.commands.verify_postgres.connection")
    def test_accepts_postgresql_18(self, connection: MagicMock) -> None:
        """PostgreSQL 18 返回成功并输出服务端版本。"""
        connection.vendor = "postgresql"
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = ("180006",)
        stdout = StringIO()

        call_command("verify_postgres", stdout=stdout)

        self.assertIn("18.6", stdout.getvalue())

    @patch("core.management.commands.verify_postgres.connection")
    def test_rejects_postgresql_17(self, connection: MagicMock) -> None:
        """低于 18 的 PostgreSQL 服务端被拒绝。"""
        connection.vendor = "postgresql"
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = ("170010",)

        with self.assertRaises(CommandError):
            call_command("verify_postgres")

    @patch("core.management.commands.verify_postgres.connection")
    def test_rejects_non_postgresql_backend(self, connection: MagicMock) -> None:
        """任何非 PostgreSQL 连接都被拒绝。"""
        connection.vendor = "mysql"

        with self.assertRaises(CommandError):
            call_command("verify_postgres")
