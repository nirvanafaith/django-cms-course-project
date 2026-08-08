"""演示数据生成命令（对应《详细设计文档》§5.5，FR-DEMO-01）。

用法：python manage.py seed_data

设计要点：
- 栏目 5 个：通知公告/教学动态/科研进展/学生活动/失物招领
- 文章 63 篇，标题关键词覆盖 "Python/课程/通知/考试/论文/基金/获奖/比赛/讲座/公告"
- 时间分布 2023-01 ~ 2026-08 各年均有（时间查询演示点）
- 含 3 篇 is_published=False 草稿（验证前台不可见）
- 固定随机种子（可复现，T-SYS-01 幂等：重复执行不产生重复数据）
"""

import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import Category, Item

# 栏目定义：(名称, 简介, 文章数)
CATEGORIES = [
    ("通知公告", "学校与学院级公告", 15),
    ("教学动态", "课程与教学安排", 12),
    ("科研进展", "科研项目与成果", 14),
    ("学生活动", "校园活动与赛事", 12),
    ("失物招领", "失物与招领信息", 10),
]

# 标题关键词（便于三种查询模式演示）
KEYWORDS = ["Python", "课程", "通知", "考试", "论文", "基金", "获奖", "比赛", "讲座", "公告"]

# 时间范围：2023-01-01 ~ 2026-08-31
TIME_START = datetime(2023, 1, 1, tzinfo=timezone.get_current_timezone())
TIME_END = datetime(2026, 8, 31, tzinfo=timezone.get_current_timezone())

RANDOM_SEED = 20260808  # 固定种子 → 每次运行生成相同数据（可复现）


class Command(BaseCommand):
    """生成 CMS 演示数据（幂等：已有数据则跳过，不重复生成）。"""

    help = "生成演示数据（栏目 5 个、文章 63 篇），重复执行不会产生重复数据"

    def handle(self, *args, **options):
        if Category.objects.exists():
            self.stdout.write(self.style.WARNING(
                f"数据已存在（栏目 {Category.objects.count()} 个、"
                f"文章 {Item.objects.count()} 篇），跳过生成（幂等，T-SYS-01）"
            ))
            return

        rng = random.Random(RANDOM_SEED)  # 固定种子，保证可复现
        total_items = 0
        draft_count = 3  # 草稿数量（前台不可见验证点）

        for name, desc, count in CATEGORIES:
            cat, _ = Category.objects.get_or_create(name=name, defaults={"description": desc})
            for i in range(count):
                # 标题：关键词 + 序号 + 栏目名
                kw = rng.choice(KEYWORDS)
                title = f"{kw}·{name}·第{i + 1}期"
                # 发布时间：范围内随机
                delta = rng.random() * (TIME_END - TIME_START)
                publish_time = TIME_START + delta
                # 前 3 篇设为草稿（分散在栏目中）
                is_published = not (total_items < draft_count)
                Item.objects.create(
                    title=title,
                    content=self._content(name, kw),
                    category=cat,
                    publish_time=publish_time,
                    is_published=is_published,
                )
                total_items += 1

        self.stdout.write(self.style.SUCCESS(
            f"演示数据生成完成：栏目 {Category.objects.count()} 个，"
            f"文章 {Item.objects.count()} 篇（含草稿 {draft_count} 篇）"
        ))

    def _content(self, cat_name, keyword):
        """生成一段可读的正文（含关键词与栏目名）。"""
        return (
            f"本篇文章属于「{cat_name}」栏目，围绕关键词「{keyword}」展开。"
            "这是 CMS 原型系统的演示数据，用于展示栏目/文章管理、"
            "前台浏览与三种查询模式（按题目、按发表时间、按栏目）的功能效果。"
            "正文内容为随机生成，不包含任何真实个人信息（NFR-09 合规）。"
        )
