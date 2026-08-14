"""验证运行数据库类型与 PostgreSQL 服务端版本。"""

from typing import Final

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

MINIMUM_VERSION_NUMBER: Final = 180000


class Command(BaseCommand):
    """拒绝非 PostgreSQL 或低于 18 的数据库服务端。"""

    help = "验证当前数据库为 PostgreSQL 18 或更高版本"

    def handle(self, *args, **options) -> None:
        if connection.vendor != "postgresql":
            raise CommandError("数据库后端必须是 PostgreSQL")

        with connection.cursor() as cursor:
            cursor.execute("SHOW server_version_num")
            version_number = int(cursor.fetchone()[0])

        if version_number < MINIMUM_VERSION_NUMBER:
            raise CommandError("PostgreSQL 服务端版本必须不低于 18")

        major = version_number // 10000
        minor = version_number % 10000
        self.stdout.write(f"PostgreSQL {major}.{minor} 验证通过")
