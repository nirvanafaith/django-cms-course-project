"""启动前检查数据库、缓存与部署安全设置。"""

from django.core.cache import cache
from django.core.checks import Tags, run_checks
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connections
from redis.exceptions import RedisError


class Command(BaseCommand):
    """在启动服务前验证关键依赖。"""

    help = "检查数据库、缓存和公网部署配置"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--mode", choices=("local", "public"), default="local")

    def handle(self, *args, **options) -> None:
        mode = options["mode"]
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
        except DatabaseError as error:
            raise CommandError("数据库不可用，请检查 MySQL 配置和服务状态") from error

        try:
            cache.set("cms:preflight", "ok", timeout=5)
            if cache.get("cms:preflight") != "ok":
                raise CommandError("缓存写入后无法正确读取")
        except (ConnectionError, RedisError) as error:
            if mode == "public":
                raise CommandError("公网模式要求 Redis 可用") from error
            self.stdout.write(self.style.WARNING("Redis 不可用，本地模式将使用降级缓存"))

        if mode == "public":
            issues = run_checks(tags=[Tags.security], include_deployment_checks=True)
            serious = [issue for issue in issues if issue.is_serious()]
            if serious:
                raise CommandError("Django 公网部署安全检查未通过")
        self.stdout.write(self.style.SUCCESS("启动前检查通过"))
