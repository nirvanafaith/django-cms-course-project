"""事务化同步北交大风格演示数据。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum, auto
from typing import Final, assert_never

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from content.demo_data import ARTICLE_SPECS, CATEGORY_SPECS, USER_SPECS, UserSpec
from content.models import Category, Item


class SyncResult(Enum):
    """单条演示记录的同步结果。"""

    CREATED = auto()
    UPDATED = auto()
    SKIPPED = auto()


@dataclass(frozen=True, slots=True)
class SyncCounts:
    """汇总一次命令执行中的同步结果。"""

    created: int = 0
    updated: int = 0
    skipped: int = 0

    def add(self, result: SyncResult) -> SyncCounts:
        """返回累计一条同步结果后的新值。"""
        match result:
            case SyncResult.CREATED:
                return SyncCounts(self.created + 1, self.updated, self.skipped)
            case SyncResult.UPDATED:
                return SyncCounts(self.created, self.updated + 1, self.skipped)
            case SyncResult.SKIPPED:
                return SyncCounts(self.created, self.updated, self.skipped + 1)
            case unreachable:
                assert_never(unreachable)


USER_PASSWORD_ENVIRONMENT: Final = "DEMO_USER_PASSWORD"
ADMIN_USERNAME: Final = "CTX"
ADMIN_PASSWORD: Final = "1234"
LEGACY_ADMIN_USERNAMES: Final = ("cms_admin", "content_admin")


def _normal_user_password() -> str:
    """在任何数据库写入前读取普通演示用户密码。"""
    value = os.environ.get(USER_PASSWORD_ENVIRONMENT)
    if not value:
        raise CommandError(f"缺少必需的演示密码环境变量：{USER_PASSWORD_ENVIRONMENT}")
    return value


def _sync_user(spec: UserSpec, password: str) -> tuple[User, SyncResult]:
    """按用户名同步角色和密码。"""
    existing = User.objects.filter(username=spec.username).first()
    if (
        existing is not None
        and existing.is_staff is spec.is_admin
        and existing.is_superuser is spec.is_admin
        and existing.is_active
        and existing.check_password(password)
    ):
        return existing, SyncResult.SKIPPED

    user, created = User.objects.update_or_create(
        username=spec.username,
        defaults={
            "is_active": True,
            "is_staff": spec.is_admin,
            "is_superuser": spec.is_admin,
        },
    )
    if created or not user.check_password(password):
        user.set_password(password)
        user.save(update_fields=["password"])
    return user, SyncResult.CREATED if created else SyncResult.UPDATED


class Command(BaseCommand):
    """同步用户、栏目和文章，重复执行不会产生重复记录。"""

    help = "同步 3 个用户、8 个栏目和 36 篇北交大风格演示文章"

    def handle(self, *args: str, **options: str) -> None:
        normal_user_password = _normal_user_password()
        counts = SyncCounts()

        with transaction.atomic():
            users: dict[str, User] = {}
            for spec in USER_SPECS:
                password = ADMIN_PASSWORD if spec.is_admin else normal_user_password
                user, result = _sync_user(spec, password)
                users[spec.username] = user
                counts = counts.add(result)

            administrator = users[ADMIN_USERNAME]
            Item.objects.filter(author__username__in=LEGACY_ADMIN_USERNAMES).update(
                author=administrator
            )
            User.objects.filter(username__in=LEGACY_ADMIN_USERNAMES).delete()

            categories: dict[str, Category] = {}
            for spec in CATEGORY_SPECS:
                existing = Category.objects.filter(name=spec.name).first()
                if existing is not None and existing.description == spec.description:
                    category, result = existing, SyncResult.SKIPPED
                else:
                    category, created = Category.objects.update_or_create(
                        name=spec.name,
                        defaults={"description": spec.description},
                    )
                    result = SyncResult.CREATED if created else SyncResult.UPDATED
                categories[spec.name] = category
                counts = counts.add(result)

            for spec in ARTICLE_SPECS:
                category = categories[spec.category_name]
                author = administrator
                existing = (
                    Item.objects.select_related("author")
                    .filter(title=spec.title, category=category)
                    .first()
                )
                is_current = (
                    existing is not None
                    and existing.content == spec.content
                    and existing.publish_time == spec.publish_time
                    and existing.is_published is spec.is_published
                    and existing.author == author
                )
                if is_current:
                    result = SyncResult.SKIPPED
                else:
                    _, created = Item.objects.update_or_create(
                        title=spec.title,
                        category=category,
                        defaults={
                            "author": author,
                            "content": spec.content,
                            "is_published": spec.is_published,
                            "publish_time": spec.publish_time,
                        },
                    )
                    result = SyncResult.CREATED if created else SyncResult.UPDATED
                counts = counts.add(result)

        draft_count = sum(not spec.is_published for spec in ARTICLE_SPECS)
        self.stdout.write(
            self.style.SUCCESS(
                f"演示数据同步完成：创建 {counts.created}，更新 {counts.updated}，"
                f"跳过 {counts.skipped}，草稿 {draft_count}"
            )
        )
