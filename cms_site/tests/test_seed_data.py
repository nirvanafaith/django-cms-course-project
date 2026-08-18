"""北交大风格演示数据命令合同测试。"""

import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from content.models import Category, Item

EXPECTED_CATEGORIES = {
    "交大头条",
    "通知公告",
    "教学科研",
    "校园动态",
    "招生就业",
    "学术活动",
    "国际交流",
    "信息公开",
}
EXPECTED_TITLES = {
    "交通强国建设专题研讨会在校举行",
    "学校召开新学期重点工作部署会",
    "轨道交通自主创新成果集中发布",
    "知行育人计划启动仪式顺利举行",
    "校园开放日展示学科建设新进展",
    "关于秋季学期开学安排的通知",
    "图书馆暑期开放时间调整公告",
    "校园网络维护与服务暂停通知",
    "研究生奖学金材料提交提醒",
    "实验室安全检查工作通知",
    "智能交通课程群完成教学改革验收",
    "本科生科研训练项目开始申报",
    "计算机基础课程开放实践周报名",
    "教师教学能力提升工作坊举行",
    "跨学科培养方案发布试行",
    "校园文化节系列活动正式启动",
    "学生创新创业成果展开幕",
    "志愿服务项目交流会圆满结束",
    "秋季运动会报名通道开放",
    "社团招新服务周安排发布",
    "本科招生线上咨询活动启动",
    "研究生招生政策宣讲会预告",
    "毕业生校园双选会参会指南",
    "国际学生入学服务手册发布",
    "轨道交通前沿学术论坛预告",
    "人工智能与工程教育讲座举行",
    "青年学者交叉论坛征集报告",
    "城市交通治理专题报告会开放预约",
    "国际合作伙伴周活动日程发布",
    "海外交流项目线上说明会举行",
    "留学生文化交流活动报名开始",
    "联合培养项目申请指南更新",
    "年度信息公开报告正式发布",
    "校级规章制度目录完成更新",
    "公共服务事项办事指南发布",
    "校园数据开放目录新增资源",
}
SEED_ENV = {
    "DEMO_USER_PASSWORD": "User-pass-2026!",
}


class SeedDataTests(TestCase):
    """验证数据规模、角色、正文、时间与重复执行行为。"""

    def test_requires_the_normal_user_password_environment_variable(self) -> None:
        """缺少普通用户密码时不写入部分数据。"""
        incomplete_environments = ({},)

        for environment in incomplete_environments:
            with (
                self.subTest(environment=environment),
                patch.dict(os.environ, environment, clear=True),
                self.assertRaises(CommandError),
            ):
                call_command("seed_data")

        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)

    def test_creates_exact_categories_titles_and_drafts(self) -> None:
        """一次执行生成批准的八栏、三十六篇和三篇草稿。"""
        with patch.dict(os.environ, SEED_ENV, clear=True):
            call_command("seed_data")

        self.assertEqual(set(Category.objects.values_list("name", flat=True)), EXPECTED_CATEGORIES)
        self.assertEqual(set(Item.objects.values_list("title", flat=True)), EXPECTED_TITLES)
        self.assertEqual(Item.objects.count(), 36)
        self.assertEqual(Item.objects.filter(is_published=False).count(), 3)

    def test_syncs_ctx_administrator_password_roles_and_authors(self) -> None:
        """普通用户和 CTX 管理员角色、密码及文章作者均正确。"""
        with patch.dict(os.environ, SEED_ENV, clear=True):
            call_command("seed_data")

        users = {user.username: user for user in User.objects.order_by("username")}
        self.assertEqual(set(users), {"student", "visitor", "CTX"})
        for username in ("student", "visitor"):
            self.assertFalse(users[username].is_staff)
            self.assertFalse(users[username].is_superuser)
            self.assertTrue(users[username].check_password(SEED_ENV["DEMO_USER_PASSWORD"]))
        self.assertTrue(users["CTX"].is_staff)
        self.assertTrue(users["CTX"].is_superuser)
        self.assertTrue(users["CTX"].check_password("1234"))
        self.assertEqual(
            set(Item.objects.values_list("author__username", flat=True)),
            {"CTX"},
        )

    def test_repeated_runs_are_idempotent_and_keep_three_paragraph_bodies(self) -> None:
        """重复执行保持精确计数，正文和时间仍满足演示合同。"""
        first_output = StringIO()
        second_output = StringIO()
        with patch.dict(os.environ, SEED_ENV, clear=True):
            call_command("seed_data", stdout=first_output)
            call_command("seed_data", stdout=second_output)

        self.assertEqual(Category.objects.count(), 8)
        self.assertEqual(Item.objects.count(), 36)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Item.objects.filter(is_published=False).count(), 3)
        self.assertTrue(all(len(item.content.split("\n\n")) == 3 for item in Item.objects.all()))
        self.assertEqual(
            {value.year for value in Item.objects.values_list("publish_time", flat=True)},
            {2023, 2024, 2025, 2026},
        )
        self.assertIn("创建 47，更新 0，跳过 0，草稿 3", first_output.getvalue())
        self.assertIn("创建 0，更新 0，跳过 47，草稿 3", second_output.getvalue())

    def test_repeated_run_repairs_existing_seed_records(self) -> None:
        """自然键已存在时同步字段，而不是把损坏状态当作已完成。"""
        with patch.dict(os.environ, SEED_ENV, clear=True):
            call_command("seed_data")

        self.assertTrue(User.objects.filter(username="student").exists())
        student = User.objects.get(username="student")
        student.is_staff = True
        student.is_superuser = True
        student.set_unusable_password()
        student.save(update_fields=["is_staff", "is_superuser", "password"])

        category = Category.objects.get(name="交大头条")
        category.description = "损坏的栏目简介"
        category.save(update_fields=["description"])

        item = Item.objects.get(title="交通强国建设专题研讨会在校举行")
        expected_publish_state = item.is_published
        item.content = "损坏的正文"
        item.is_published = not expected_publish_state
        item.author = student
        item.save(update_fields=["content", "is_published", "author"])

        output = StringIO()
        with patch.dict(os.environ, SEED_ENV, clear=True):
            call_command("seed_data", stdout=output)

        student.refresh_from_db()
        category.refresh_from_db()
        item.refresh_from_db()
        self.assertFalse(student.is_staff)
        self.assertFalse(student.is_superuser)
        self.assertTrue(student.check_password(SEED_ENV["DEMO_USER_PASSWORD"]))
        self.assertNotEqual(category.description, "损坏的栏目简介")
        self.assertEqual(len(item.content.split("\n\n")), 3)
        self.assertEqual(item.is_published, expected_publish_state)
        self.assertEqual(item.author.username, "CTX")
        self.assertIn("创建 0，更新 3，跳过 44，草稿 3", output.getvalue())

    def test_repeated_run_replaces_obsolete_seed_administrators(self) -> None:
        """旧演示管理员的文章在删除账号前转交给 CTX。"""
        legacy_admin = User.objects.create_superuser("cms_admin", password="legacy-password")
        category = Category.objects.create(name="旧管理员栏目")
        item = Item.objects.create(
            title="旧管理员文章", content="正文", category=category, author=legacy_admin
        )

        with patch.dict(os.environ, SEED_ENV, clear=True):
            call_command("seed_data")

        item.refresh_from_db()
        self.assertEqual(item.author.username, "CTX")
        self.assertFalse(User.objects.filter(username="cms_admin").exists())
