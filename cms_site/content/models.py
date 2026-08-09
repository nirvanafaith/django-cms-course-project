"""content 应用模型定义（对应《详细设计文档》§5）。

实体：
- Category：栏目（名称唯一、可带简介）
- Item：文章（标题/正文/栏目/发表时间/发布状态/作者）

删除策略（裁决 D-3'，见《技术报告》§6.1）：Category 外键 on_delete=PROTECT——
有文章的栏目禁止删除（FR-CAT-03），删除时抛 ProtectedError 由调用方捕获提示。

BCNF 说明（《技术报告》§4）：两表均为单列主键、属性直接依赖主键，
表内不存在对非键属性的部分/传递依赖，满足 BCNF。
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class ItemQuerySet(models.QuerySet):
    """文章查询集合，集中保存可被多个页面复用的数据访问规则。

    Django QuerySet 采用惰性求值：调用 ``published()`` 只会继续构造 SQL，直到
    模板遍历、调用 ``list()`` 或执行 ``exists()`` 等操作时才真正访问数据库。
    因此该方法既能复用“草稿不可见”规则，也不会提前加载无用数据。
    """

    def published(self):
        """返回前台允许公开展示的文章，并保留 QuerySet 的链式调用能力。"""
        return self.filter(is_published=True)


class Category(models.Model):
    """栏目（文章的分类目录）。"""

    name = models.CharField("栏目名称", max_length=50, unique=True)
    description = models.TextField("栏目简介", blank=True, null=True)
    created_at = models.DateTimeField("建立时间", auto_now_add=True)

    class Meta:
        verbose_name = "栏目"
        verbose_name_plural = "栏目"
        # 与已提交迁移保持同一序列表示；它只影响默认排序，不新增数据库字段。
        ordering = ["id"]  # noqa: RUF012 - must match the committed migration

    def __str__(self):
        return self.name


class Item(models.Model):
    """文章（内容条目）。"""

    # as_manager() 把 QuerySet 方法暴露为 Item.objects.published()。
    # Manager 只改变 Python 查询接口，不增加数据库字段，所以不会产生迁移。
    objects = ItemQuerySet.as_manager()

    title = models.CharField("标题", max_length=200)
    content = models.TextField("正文", blank=True)  # 正文允许空串（设计取舍 D-06）
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
    is_published = models.BooleanField("发布状态", default=True)  # 草稿前台不可见（FR-ART-05）
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="作者",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # 作者删除后保留文章（作者可空）
    )

    class Meta:
        verbose_name = "文章"
        verbose_name_plural = "文章"
        # 最新文章优先；列表形式与初始迁移保持一致。
        ordering = ["-publish_time"]  # noqa: RUF012 - must match the committed migration

    def __str__(self):
        return self.title
