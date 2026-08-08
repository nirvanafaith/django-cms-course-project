"""Admin 集成测试（对应《测试文档》§6.3 T-ADM-01~06）。

覆盖：
- T-ADM-01 未登录访问 /admin/ → 重定向登录页
- T-ADM-02 管理员发布文章 → 保存成功，前台可见
- T-ADM-03 管理员改文章 → 前台显示新标题
- T-ADM-04 管理员删文章 → 前台详情 404
- T-ADM-05 删除有文章栏目 → 被阻止（ProtectedError）
- T-ADM-06 非 staff 登录访问 → 403/拒绝
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from content.models import Category, Item


def _make_staff():
    """创建 staff 管理员（后台管理权限，授予 content 应用全部模型权限）。"""
    user = get_user_model().objects.create_user(
        username="admin1", password="pass12345", is_staff=True
    )
    perms = Permission.objects.filter(content_type__app_label="content")
    user.user_permissions.add(*perms)
    return user


def _make_normal_user():
    """创建普通用户（无后台权限）。"""
    return get_user_model().objects.create_user(
        username="normal1", password="pass12345"
    )


class AdminAuthTests(TestCase):
    """T-ADM-01 / T-ADM-06：后台权限控制。"""

    def test_tadm01_anonymous_redirected_to_login(self):
        """T-ADM-01：未登录访问 /admin/ 重定向到登录页。"""
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login/", resp.url)

    def test_tadm06_non_staff_rejected(self):
        """T-ADM-06：普通用户登录后访问 /admin/ 被拒绝。"""
        _make_normal_user()
        self.client.login(username="normal1", password="pass12345")
        resp = self.client.get("/admin/")
        self.assertIn(resp.status_code, (302, 403))  # 拒绝访问

    def test_tadm06b_staff_can_access(self):
        """T-ADM-06 补充：staff 登录后正常访问后台。"""
        _make_staff()
        self.client.login(username="admin1", password="pass12345")
        resp = self.client.get("/admin/")
        self.assertEqual(resp.status_code, 200)


class AdminCrudTests(TestCase):
    """T-ADM-02~05：管理员 CRUD 闭环。"""

    @classmethod
    def setUpTestData(cls):
        cls.staff = _make_staff()
        cls.cat = Category.objects.create(name="教学动态")

    def setUp(self):
        self.client.login(username="admin1", password="pass12345")

    def test_tadm02_publish_item(self):
        """T-ADM-02：管理员发布文章 → 保存成功，前台列表可见。"""
        resp = self.client.post(
            "/admin/content/item/add/",
            {
                "title": "管理员发布的文章",
                "content": "正文内容",
                "category": self.cat.pk,
                "publish_time_0": "2026-08-08",  # Admin 拆分日期组件
                "publish_time_1": "10:00:00",
                "is_published": "on",
                "_save": "保存",
            },
        )
        self.assertEqual(resp.status_code, 302)  # 保存后重定向
        item = Item.objects.get(title="管理员发布的文章")
        self.assertTrue(item.is_published)
        # 前台可见
        resp = self.client.get(reverse("content:index"))
        self.assertContains(resp, "管理员发布的文章")

    def test_tadm03_update_item_title(self):
        """T-ADM-03：管理员改文章标题 → 前台显示新标题。"""
        item = Item.objects.create(title="旧标题", content="正文", category=self.cat)
        resp = self.client.post(
            f"/admin/content/item/{item.pk}/change/",
            {
                "title": "新标题",
                "content": "正文",
                "category": self.cat.pk,
                "publish_time_0": item.publish_time.strftime("%Y-%m-%d"),
                "publish_time_1": item.publish_time.strftime("%H:%M:%S"),
                "is_published": "on",
                "_save": "保存",
            },
        )
        self.assertEqual(resp.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.title, "新标题")
        resp = self.client.get(reverse("content:index"))
        self.assertContains(resp, "新标题")

    def test_tadm04_delete_item(self):
        """T-ADM-04：管理员删文章 → 前台详情 404。"""
        item = Item.objects.create(title="待删除", content="正文", category=self.cat)
        # 先确认详情 200
        self.assertEqual(self.client.get(reverse("content:item_detail", args=[item.pk])).status_code, 200)
        # 删除（带确认）
        resp = self.client.post(f"/admin/content/item/{item.pk}/delete/", {"post": "yes"})
        self.assertEqual(resp.status_code, 302)
        # 前台 404
        resp = self.client.get(reverse("content:item_detail", args=[item.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_tadm05_delete_category_with_items_blocked(self):
        """T-ADM-05：删除有文章栏目被阻止（ProtectedError），栏目仍在。"""
        Item.objects.create(title="保护文章", content="正文", category=self.cat)
        resp = self.client.post(
            f"/admin/content/category/{self.cat.pk}/delete/", {"post": "yes"}
        )
        # Admin 对被引用对象：不删除、返回非 302（停留在确认/错误页）
        self.assertNotEqual(resp.status_code, 302)
        self.assertTrue(Category.objects.filter(pk=self.cat.pk).exists())

    def test_tadm07_batch_publish_and_draft_actions(self):
        """T-ADM-07 补充：自定义 Action 批量发布/撤回（加分项，设计 §8）。"""
        # 3 篇草稿 → 批量发布
        items = [
            Item.objects.create(title=f"草稿{i}", content="正文", category=self.cat, is_published=False)
            for i in range(3)
        ]
        ids = [i.pk for i in items]
        resp = self.client.post(
            "/admin/content/item/",
            {"action": "mark_published", "_selected_action": ids},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(all(Item.objects.get(pk=pk).is_published for pk in ids))
        # 批量撤回为草稿
        resp = self.client.post(
            "/admin/content/item/",
            {"action": "mark_draft", "_selected_action": ids},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(all(not Item.objects.get(pk=pk).is_published for pk in ids))
        # 前台均不可见
        for pk in ids:
            self.assertEqual(self.client.get(reverse("content:item_detail", args=[pk])).status_code, 404)
