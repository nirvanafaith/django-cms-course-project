"""content 应用模型定义（对应《详细设计文档》§5）。

实体：
- Category：栏目（名称唯一、可带简介）
- Item：文章（标题/正文/栏目/发表时间/发布状态/作者）

删除策略（裁决 D-3'，见《技术报告》§6.1）：Category 外键 on_delete=PROTECT——
有文章的栏目禁止删除（FR-CAT-03），删除时抛 ProtectedError 由调用方捕获提示。

BCNF 说明（《技术报告》§4）：两表均为单列主键、属性直接依赖主键，
表内不存在对非键属性的部分/传递依赖，满足 BCNF。
"""

from __future__ import annotations

from typing import ClassVar

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.db import models
from django.db.models import Q
from django.db.models.functions import Upper
from django.utils import timezone


class ItemQuerySet(models.QuerySet["Item"]):
    """文章查询集合，集中保存可被多个页面复用的数据访问规则。

    Django QuerySet 采用惰性求值：调用 ``published()`` 只会继续构造 SQL，直到
    模板遍历、调用 ``list()`` 或执行 ``exists()`` 等操作时才真正访问数据库。
    因此该方法既能复用“草稿不可见”规则，也不会提前加载无用数据。
    """

    def published(self):
        """返回前台允许公开展示的文章，并保留 QuerySet 的链式调用能力。"""
        return self.filter(is_published=True)


class ItemManager(models.Manager["Item"]):
    """暴露带类型信息的文章查询集合入口。"""

    def get_queryset(self) -> ItemQuerySet:
        """返回文章专用查询集合。"""
        return ItemQuerySet(self.model, using=self._db)

    def published(self) -> ItemQuerySet:
        """返回前台允许公开展示的文章。"""
        return self.get_queryset().published()


class Category(models.Model):
    """栏目（文章的分类目录）。"""

    name = models.CharField("栏目名称", max_length=50, unique=True)
    description = models.TextField("栏目简介", blank=True, null=True)  # noqa: DJ001
    created_at = models.DateTimeField("建立时间", auto_now_add=True)

    class Meta:
        verbose_name = "栏目"
        verbose_name_plural = "栏目"
        # 与已提交迁移保持同一序列表示；它只影响默认排序，不新增数据库字段。
        ordering = ["id"]  # noqa: RUF012 - must match the committed migration

    def __str__(self):
        return str(self.name)


class Item(models.Model):
    """文章（内容条目）。"""

    title = models.CharField("标题", max_length=200)
    content = models.TextField("正文")
    category = models.ForeignKey(
        Category,
        verbose_name="所属栏目",
        on_delete=models.PROTECT,  # 裁决 D-3'：有文章栏目禁删（FR-CAT-03）
        related_name="items",
    )
    publish_time = models.DateTimeField(
        "发表时间",
        default=timezone.now,  # 按时间查询目标字段，建索引（设计 §5.3）
        db_index=True,
    )
    updated_at = models.DateTimeField("最后修改时间", auto_now=True)
    is_published = models.BooleanField("发布状态", default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="作者",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # 作者删除后保留文章（作者可空）
    )

    # Manager 只改变 Python 查询接口，不增加数据库字段。
    objects = ItemManager()

    class Meta:
        verbose_name = "文章"
        verbose_name_plural = "文章"
        ordering: ClassVar[list[str]] = ["-publish_time", "-pk"]
        indexes: ClassVar[list[models.Index]] = [
            models.Index(
                fields=["is_published", "-publish_time"],
                name="item_pub_time_idx",
            ),
            models.Index(
                fields=["category", "is_published", "-publish_time"],
                name="item_cat_pub_time_idx",
            ),
            GinIndex(
                OpClass(Upper("title"), name="gin_trgm_ops"),
                condition=Q(is_published=True),
                name="item_title_trgm_idx",
            ),
        ]

    def __str__(self):
        return str(self.title)
