"""content 应用 Admin 注册（对应《详细设计文档》§8）。

配置要点：
- CategoryAdmin：列表显示 名称/文章数/建立时间；按名称搜索
- ItemAdmin：列表显示 标题/栏目/发表时间/发布状态；list_filter/search_fields/date_hierarchy
  与前台三种查询模式对应（可作功能演示素材）；
  字段顺序 title → category → content → is_published → publish_time（§6.2）
- 自定义 Action：mark_published / mark_draft（批量发布/撤回，加分项）
- 只读字段：Category.created_at / Item.updated_at（自动维护，禁改）
"""

from django.contrib import admin
from django.db.models import Count

from .models import Category, Item


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """栏目管理（FR-CAT-01~04）。"""

    list_display = ("name", "article_count", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at",)
    ordering = ("id",)

    def get_queryset(self, request):
        """为后台列表附加文章总数，避免每行再执行一次 Count 查询。

        这里统计全部文章，包含草稿；后台管理员需要知道栏目中实际保存了多少
        条内容，这与前台只统计已发布文章的 selector 是两个有意不同的业务语义。
        """
        return super().get_queryset(request).annotate(_item_count=Count("items"))

    @admin.display(description="文章数")
    def article_count(self, obj):
        """读取 ``get_queryset`` 预先 annotate 的计数，避免再次访问数据库。"""
        return getattr(obj, "_item_count", 0)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """文章管理（FR-ART-01~05）。"""

    list_display = ("title", "category", "publish_time", "is_published")
    list_filter = ("is_published", "category", "publish_time")  # 与前台三查询模式对应
    search_fields = ("title",)
    date_hierarchy = "publish_time"
    readonly_fields = ("updated_at",)
    list_per_page = 20
    actions = ("mark_published", "mark_draft")  # tuple 满足 RUF012（可变默认值）

    @admin.action(description="设为已发布")
    def mark_published(self, request, queryset):
        """用一次批量 UPDATE 发布选中文章，并向管理员反馈影响行数。"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f"已将 {updated} 篇文章设为发布")

    @admin.action(description="设为草稿")
    def mark_draft(self, request, queryset):
        """用一次批量 UPDATE 撤回文章；撤回后前台 selector 将自动隐藏它们。"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f"已将 {updated} 篇文章设为草稿")
