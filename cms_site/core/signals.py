"""内容变更后的缓存失效信号。"""

from __future__ import annotations

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from content.models import Category, Item

from .caching import invalidate_home, invalidate_item


@receiver(post_save, sender=Item)
@receiver(post_delete, sender=Item)
def item_changed(sender, instance: Item, **kwargs) -> None:
    """文章提交保存或删除后失效相关缓存。"""
    pk = instance.pk
    if pk is not None:
        transaction.on_commit(lambda: invalidate_item(pk))


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def category_changed(sender, instance: Category, **kwargs) -> None:
    """栏目提交保存或删除后失效首页缓存。"""
    transaction.on_commit(invalidate_home)
