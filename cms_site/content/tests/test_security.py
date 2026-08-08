"""安全测试（对应《测试文档》§6.4 T-SEC-01~06）。

覆盖：
- T-SEC-01 SQL 注入样例（q 含注入片段不返回全表）
- T-SEC-02 注入组合场景（日期参数注入 → 校验失败友好提示）
- T-SEC-03 XSS 转义（正文含 <script> 被转义）
- T-SEC-04 CSRF 保护（无 token POST → 403）
- T-SEC-05 越权访问详情（草稿 → 404）
- T-SEC-06 会话 Cookie 属性（HttpOnly / SameSite）
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Category, Item


class SecurityTests(TestCase):
    """T-SEC-01~06：注入 / XSS / CSRF / 越权 / 会话安全。"""

    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name="教学动态")
        cls.item = Item.objects.create(
            title="安全测试文章",
            content="<script>alert(1)</script> 安全正文",
            category=cls.cat,
            publish_time=timezone.now(),
        )
        cls.draft = Item.objects.create(
            title="越权草稿",
            content="草稿正文",
            category=cls.cat,
            is_published=False,
            publish_time=timezone.now(),
        )

    def test_tsec01_sql_injection_sample(self):
        """T-SEC-01：q 含注入片段 ' OR 1=1 -- → 结果集为空/无异常，不返回全表。"""
        resp = self.client.get(reverse("content:search"), {"q": "' OR 1=1 --"})
        self.assertEqual(resp.status_code, 200)
        # 不返回所有文章（全表仅 1 篇已发布，若注入生效会全部返回）
        self.assertNotContains(resp, "越权草稿")
        # 参数化查询：注入片段被当作字面量，无匹配
        self.assertContains(resp, "没有找到")

    def test_tsec02_injection_date_parameter(self):
        """T-SEC-02：日期参数注入 → 表单校验失败，友好提示而非 500。"""
        resp = self.client.get(
            reverse("content:search"), {"start": "2026-01-01' OR '1'='1"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "日期格式应为 YYYY-MM-DD")

    def test_tsec03_xss_escaped(self):
        """T-SEC-03：正文含 <script> 在详情页被转义为 &lt;script&gt;。"""
        resp = self.client.get(reverse("content:item_detail", args=[self.item.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "&lt;script&gt;")  # 被转义
        self.assertNotContains(resp, "<script>alert(1)</script>")  # 原始脚本不出现

    def test_tsec04_csrf_protection(self):
        """T-SEC-04：无 CSRF token 的 POST → 403 拒绝。

        Django 测试客户端默认不强制 CSRF 校验，需用 enforce_csrf_checks=True 的客户端验证。
        """
        from django.test import Client as CsrfClient

        csrf_client = CsrfClient(enforce_csrf_checks=True)
        resp = csrf_client.post("/admin/login/", {"username": "x", "password": "y"})
        self.assertEqual(resp.status_code, 403)

    def test_tsec05_unauthorized_draft_access(self):
        """T-SEC-05：普通用户访问草稿详情 → 404（视同不存在）。"""
        resp = self.client.get(reverse("content:item_detail", args=[self.draft.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_tsec06_session_cookie_attributes(self):
        """T-SEC-06：会话 Cookie 属性 HttpOnly / SameSite=Lax 已配置（NFR-02）。

        settings 中显式配置（见 config/settings.py 会话安全段）：
        SESSION_COOKIE_HTTPONLY=True、SESSION_COOKIE_SAMESITE="Lax"。
        """
        from django.conf import settings

        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
