"""北交大风格前台与 Admin 模板合同测试。"""

from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from content.demo_data import CATEGORY_SPECS
from content.models import Category, Item

SHANGHAI = ZoneInfo("Asia/Shanghai")
HERO_PATHS = tuple(f"/static/img/bjtu/hero-{index:02d}.jpg" for index in range(1, 6))


@override_settings(PUBLIC_PAGE_CACHE_ENABLED=False)
class BjtuTemplateTests(TestCase):
    """验证前台结构、素材、身份入口和后台品牌。"""

    normal_user: User
    admin_user: User
    headline: Item

    @classmethod
    def setUpTestData(cls) -> None:
        """创建覆盖首页栏目分区和三种角色的最小数据。"""
        cls.normal_user = User.objects.create_user("student", password="test-password-1")
        cls.admin_user = User.objects.create_superuser(
            "cms_admin",
            email="admin@example.com",
            password="test-password-2",
        )
        categories = {
            spec.name: Category.objects.create(name=spec.name, description=spec.description)
            for spec in CATEGORY_SPECS
        }
        for index, category in enumerate(categories.values(), start=1):
            item = Item.objects.create(
                title=f"{category.name}模板合同文章",
                content="第一段课程演示正文。\n\n第二段课程演示正文。",
                category=category,
                author=cls.admin_user,
                publish_time=datetime(2026, 8, index, 9, tzinfo=SHANGHAI),
                is_published=True,
            )
            if category.name == "交大头条":
                cls.headline = item

    def test_homepage_uses_local_brand_assets_and_accessible_carousel(self) -> None:
        """首页只使用本地品牌素材并提供可控制轮播。"""
        response = self.client.get(reverse("content:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/img/bjtu/logo.png")
        for hero_path in HERO_PATHS:
            with self.subTest(hero_path=hero_path):
                self.assertContains(response, hero_path)
        self.assertContains(response, "data-carousel")
        self.assertContains(response, "data-slide", count=5)
        self.assertContains(response, "data-carousel-prev")
        self.assertContains(response, "data-carousel-next")
        self.assertContains(response, "data-carousel-toggle")
        self.assertContains(response, 'aria-live="polite"')
        self.assertNotContains(response, "cdn.jsdelivr.net")
        self.assertNotContains(response, 'src="http')

    def test_homepage_exposes_approved_semantic_sections_and_image_alt_text(self) -> None:
        """主页按批准顺序提供可辨识分区和非空替代文本。"""
        response = self.client.get(reverse("content:index"))

        for heading in (
            "交大头条",
            "教学科研",
            "校园动态",
            "通知公告",
            "校园影像",
            "专题栏目",
        ):
            with self.subTest(heading=heading):
                self.assertContains(response, f">{heading}<")
        self.assertContains(response, "<h1", html=False)
        self.assertNotContains(response, 'alt=""')

    def test_global_navigation_and_footer_match_the_approved_contract(self) -> None:
        """导航、地址、邮编、来源与非官网声明保持一致。"""
        response = self.client.get(reverse("content:index"))

        for label in ("首页", "栏目", "文章", "查询"):
            with self.subTest(label=label):
                self.assertContains(response, f">{label}<")
        self.assertContains(response, "北京市海淀区上园村3号北京交通大学")
        self.assertContains(response, "邮编：100044")
        self.assertContains(response, "课程 CMS 原型，非官方网站")
        self.assertContains(response, "北交大官网素材来源与许可")
        self.assertNotContains(response, "ICP备")

    def test_navigation_reflects_anonymous_normal_and_admin_roles(self) -> None:
        """三种身份只显示其可用入口。"""
        anonymous = self.client.get(reverse("content:index"))
        self.assertContains(anonymous, ">登录<")
        self.assertNotContains(anonymous, "退出登录")
        self.assertNotContains(anonymous, "管理后台")

        self.client.force_login(self.normal_user)
        normal = self.client.get(reverse("content:index"))
        self.assertContains(normal, "退出登录")
        self.assertNotContains(normal, "管理后台")

        self.client.force_login(self.admin_user)
        administrator = self.client.get(reverse("content:index"))
        self.assertContains(administrator, "退出登录")
        self.assertContains(administrator, "管理后台")

    def test_public_pages_have_page_specific_semantic_titles(self) -> None:
        """列表、搜索、详情和登录页面各有唯一主标题。"""
        pages = (
            (reverse("content:item_list"), "文章列表"),
            (reverse("content:search"), "文章查询"),
            (reverse("content:item_detail", args=[self.headline.pk]), self.headline.title),
            (reverse("login"), "用户登录"),
        )

        for url, heading in pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "<h1", count=1, html=False)
                self.assertContains(response, heading)

    def test_admin_uses_local_school_brand_without_replacing_admin_layout(self) -> None:
        """Admin 使用本地校名标识并保留原生应用列表。"""
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/static/img/bjtu/logo.png")
        self.assertContains(response, "北京交通大学课程 CMS 管理后台")
        self.assertContains(response, "内容管理")
        self.assertContains(response, "认证和授权")
        self.assertNotContains(response, 'src="http')
