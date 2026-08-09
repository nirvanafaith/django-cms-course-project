# CMS 前后台 UI 精修 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 Django CMS 精修为统一、响应式、可访问的编辑型内容门户，并以官方模板覆盖方式美化原生 Django Admin，同时保持全部课程功能与业务行为不变。

**Architecture:** 项目根目录的 `DESIGN.md` 是视觉决策单一事实来源；前台继续使用 Django 服务端模板与 Bootstrap 5，项目 CSS 变量负责视觉覆盖，仅用少量原生 JavaScript 实现移动导航。后台继续使用原生 Django Admin，通过 `templates/admin/base_site.html` 和独立 CSS 定制，不复制 CRUD 或权限逻辑。

**Tech Stack:** Python 3.13、Django 5.2、Django Templates、Bootstrap 5.3.3、原生 CSS/JavaScript、Django `TestCase`、Ruff、Playwright/真实 Chromium。

## Global Constraints

- 保留 `Category`、`Item`、数据库结构、现有 URL、Admin CRUD、权限、发布/草稿、查询与分页语义。
- 保留现有测试依赖的文字与行为，包括“没有找到”“共 N 页”“日期格式应为 YYYY-MM-DD”和分页查询参数。
- 不修改 `content/models.py`、迁移文件或 `content/urls.py`。
- 不引入 React、Vue、大型 JavaScript 依赖或自建后台 CRUD。
- 不在界面中使用 Apple 或其他公司的名称、标识、专有图片、专有字体或品牌文案。
- 不使用 emoji 作为图标；必要图标使用统一的内联 SVG。
- 目标为 WCAG 2.2 AA；正文对比度至少 4.5:1，所有主要操作支持键盘，触控目标约 44px。
- 动效仅使用 `transform`、`opacity`、`filter`，并尊重 `prefers-reduced-motion`。
- 所有视觉常量必须先在 `DESIGN.md` 定义，再由 CSS 令牌消费。
- 工作区已有用户未提交修改。不得还原、覆盖或暂存无关文件；用户未明确要求时不得提交 Git。
- 这是一项 Django Web UI 工作，不执行任何 Godot 项目改动。

## File Map

**Create**

- `DESIGN.md`: 视觉令牌、组件、状态、响应式和可访问性合同。
- `cms_site/static/css/tokens.css`: `DESIGN.md` 对应的 CSS 自定义属性。
- `cms_site/static/css/admin.css`: 原生 Django Admin 视觉覆盖。
- `cms_site/static/js/main.js`: 移动端主导航开关。
- `cms_site/templates/partials/nav.html`: 全局导航。
- `cms_site/templates/partials/messages.html`: 系统消息。
- `cms_site/templates/partials/pagination.html`: 保留查询参数的分页。
- `cms_site/templates/admin/base_site.html`: Admin 官方模板覆盖入口。
- `cms_site/templates/content/_showcase.html`: 不对外路由的组件状态夹具。
- `cms_site/content/tests/test_templates_frontend.py`: 前台模板、语义和状态测试。
- `cms_site/content/tests/test_templates_admin.py`: Admin 覆盖与关键页面测试。

**Modify**

- `cms_site/templates/base.html`: 可访问的全局页面壳。
- `cms_site/templates/content/index.html`: 欢迎区、栏目和最新文章。
- `cms_site/templates/content/item_list.html`: 列表、搜索结果、条件摘要和空状态。
- `cms_site/templates/content/search_form.html`: 查询帮助、错误与恢复路径。
- `cms_site/templates/content/item_detail.html`: 阅读布局和返回路径。
- `cms_site/static/css/custom.css`: 前台组件样式与响应式规则。
- `cms_site/content/views.py`: 仅补充模板呈现需要的栏目语境。
- `docs/09_操作说明书.md`: 同步改造后的前后台操作入口。
- `docs/05_测试报告.md`: 回填新增测试和视觉验证证据。
- `docs/07_AI使用说明.md`: 记录本轮 AI 使用、采纳与拒绝决策。
- `docs/02_详细设计文档.md`: 同步设计系统与 Admin 模板覆盖取舍。

## Dependency Order

1. Task 1 建立 `DESIGN.md`。
2. Task 2 锁定模板与上下文契约。
3. Task 3 建立静态资源与全局页面壳。
4. Task 4、5、6 分别完成首页、列表/搜索、详情页。
5. Task 7 美化原生 Admin。
6. Task 8 建立组件状态夹具并做设计系统合规检查。
7. Task 9 更新课程文档。
8. Task 10 完成自动化、浏览器、视觉与代码审查。

---

### Task 1: 建立项目设计系统合同

**Files:**
- Create: `DESIGN.md`
- Create: `cms_site/static/css/tokens.css`

**Interfaces:**
- Produces: 后续所有前台和 Admin CSS 使用的 `--cms-*` 令牌。
- Consumes: 已批准规格 `docs/superpowers/specs/2026-08-09-ui-refinement-design.md`。

- [ ] **Step 1: 编写 `DESIGN.md`**

必须包含 `## 0. Research Log` 以及氛围、颜色、排版、间距与布局、组件、动效、表面层级、可访问性与债务八节。记录本项目采用批准规格作为视觉合同，不复制品牌资产，不引入大型前端依赖。

颜色与基础令牌至少定义：

```css
:root {
  --cms-bg: #f6f7f9;
  --cms-surface: #ffffff;
  --cms-surface-subtle: #f0f2f5;
  --cms-border: #e4e7eb;
  --cms-border-strong: #c9ced6;
  --cms-text: #1f2329;
  --cms-text-secondary: #5b616e;
  --cms-accent: #2563eb;
  --cms-accent-strong: #1e50b8;
  --cms-accent-soft: #eaf0fd;
  --cms-danger: #b42318;
  --cms-danger-soft: #fdeceb;
  --cms-success: #15803d;
  --cms-success-soft: #e8f6ee;
  --cms-warning: #9a6700;
  --cms-warning-soft: #fdf3e0;
  --cms-font-sans: system-ui, "Segoe UI", Roboto, "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  --cms-text-sm: 0.875rem;
  --cms-text-base: 1rem;
  --cms-text-lg: 1.125rem;
  --cms-text-xl: 1.25rem;
  --cms-text-2xl: 1.5rem;
  --cms-text-3xl: 1.875rem;
  --cms-space-1: 0.25rem;
  --cms-space-2: 0.5rem;
  --cms-space-3: 0.75rem;
  --cms-space-4: 1rem;
  --cms-space-5: 1.25rem;
  --cms-space-6: 1.5rem;
  --cms-space-8: 2rem;
  --cms-space-12: 3rem;
  --cms-space-16: 4rem;
  --cms-content-max: 70rem;
  --cms-read-max: 45rem;
  --cms-radius-sm: 0.375rem;
  --cms-radius-md: 0.5rem;
  --cms-radius-lg: 0.75rem;
  --cms-motion-fast: 120ms;
  --cms-motion-base: 200ms;
  --cms-ease-out: cubic-bezier(0.2, 0, 0, 1);
}
```

- [ ] **Step 2: 定义组件状态**

在 `DESIGN.md` 第 5 节逐项记录导航、页面标题、栏目入口、文章行、元数据、搜索字段、按钮、条件摘要、分页、空状态、消息和 Admin 表单/列表的结构、变体、默认/悬停/按下/焦点/错误/禁用状态。

- [ ] **Step 3: 将令牌同步到 CSS**

把同一组 `:root` 自定义属性写入 `cms_site/static/css/tokens.css`，不得出现 `DESIGN.md` 未声明的颜色、字号或动效值。

- [ ] **Step 4: 验证合同完整性**

Run:

```powershell
rg "^## [0-8]\." DESIGN.md
rg -- "--cms-(bg|surface|text|accent|space|motion)" DESIGN.md cms_site/static/css/tokens.css
```

Expected: Research Log 与八个必需章节均出现；两处令牌名称和值一致；无 `TBD`、`TODO` 或品牌资产说明。

---

### Task 2: 锁定模板上下文与呈现契约

**Files:**
- Create: `cms_site/content/tests/test_templates_frontend.py`
- Modify: `cms_site/content/views.py`

**Interfaces:**
- Produces: `item_list` 与 `search` 上下文中的 `current_category: Category | None`。
- Preserves: 查询过滤、分页、错误处理和现有上下文键。

- [ ] **Step 1: 编写失败测试**

```python
from django.urls import reverse

from content.tests.test_views import BaseViewTests


class CategoryContextTests(BaseViewTests):
    def test_item_list_exposes_current_category(self):
        response = self.client.get(
            reverse("content:item_list"), {"category": self.cat_python.pk}
        )
        self.assertEqual(response.context["current_category"], self.cat_python)

    def test_item_list_without_category_exposes_none(self):
        response = self.client.get(reverse("content:item_list"))
        self.assertIsNone(response.context["current_category"])

    def test_search_exposes_selected_category(self):
        response = self.client.get(
            reverse("content:search"), {"category": self.cat_python.pk}
        )
        self.assertEqual(response.context["current_category"], self.cat_python)

    def test_invalid_search_exposes_none(self):
        response = self.client.get(
            reverse("content:search"), {"start": "2026-13-45"}
        )
        self.assertIsNone(response.context["current_category"])
```

- [ ] **Step 2: 验证测试先失败**

Run from `cms_site`:

```powershell
python manage.py test content.tests.test_templates_frontend.CategoryContextTests -v 2
```

Expected: FAIL，原因是 `current_category` 尚未进入上下文。

- [ ] **Step 3: 最小实现上下文**

在 `item_list()` 中初始化并注入：

```python
current_category = None
if category_id:
    qs = qs.filter(category_id=category_id)
    current_category = Category.objects.filter(pk=category_id).first()

context = {
    "page_obj": page_obj,
    "page_title": "文章列表",
    "request_query": _request_query(request),
    "current_category": current_category,
}
```

在 `search()` 中于表单判断前初始化 `current_category = None`；合法栏目过滤时赋值，并把该键加入上下文。不得改变 `SearchForm` 或过滤条件。

- [ ] **Step 4: 验证通过与回归**

```powershell
python manage.py test content.tests.test_templates_frontend.CategoryContextTests -v 2
python manage.py test content.tests.test_views -v 1
ruff check content/views.py content/tests/test_templates_frontend.py
```

Expected: 新测试与全部既有视图测试通过；Ruff 无错误。

---

### Task 3: 建立可访问的全局页面壳

**Files:**
- Create: `cms_site/templates/partials/nav.html`
- Create: `cms_site/templates/partials/messages.html`
- Create: `cms_site/templates/partials/pagination.html`
- Create: `cms_site/static/js/main.js`
- Modify: `cms_site/templates/base.html`
- Modify: `cms_site/static/css/custom.css`
- Test: `cms_site/content/tests/test_templates_frontend.py`

**Interfaces:**
- Consumes: `tokens.css`、Django `request` 与 `messages`。
- Produces: `#main-content`、主导航、移动菜单、活动页状态、消息与分页 partial。

- [ ] **Step 1: 编写失败的页面壳测试**

```python
from django.contrib.auth import get_user_model
from django.urls import reverse

from content.tests.test_views import BaseViewTests


class ShellAccessibilityTests(BaseViewTests):
    def test_index_has_skip_link_and_landmarks(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, 'href="#main-content"')
        self.assertContains(response, 'id="main-content"')
        self.assertContains(response, 'aria-label="主导航"')

    def test_active_page_is_announced(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, 'aria-current="page"')

    def test_mobile_toggle_has_expanded_contract(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, 'aria-controls="site-nav-menu"')

    def test_admin_link_is_staff_only(self):
        self.assertNotContains(
            self.client.get(reverse("content:index")), 'href="/admin/"'
        )
        user = get_user_model().objects.create_user(
            username="staff-ui", password="pass12345", is_staff=True
        )
        self.client.force_login(user)
        self.assertContains(
            self.client.get(reverse("content:index")), 'href="/admin/"'
        )
```

- [ ] **Step 2: 运行红灯测试**

```powershell
python manage.py test content.tests.test_templates_frontend.ShellAccessibilityTests -v 2
```

Expected: FAIL，现有 `base.html` 没有 skip link、移动菜单按钮或活动页 ARIA。

- [ ] **Step 3: 重构 `base.html`**

保持 `{% block title %}` 和 `{% block content %}` 名称不变。按此顺序加载 Bootstrap、`tokens.css`、`custom.css`；正文末尾延迟加载 `main.js`。结构应为：

```django
<body class="cms-body">
  {% include "partials/nav.html" %}
  <main id="main-content" class="site-main container">
    {% include "partials/messages.html" %}
    {% block content %}{% endblock %}
  </main>
  <footer class="site-footer">...</footer>
  <script src="{% static 'js/main.js' %}" defer></script>
</body>
```

保留 Bootstrap 5.3.3 CDN 作为当前实现依赖，避免在本任务中复制第三方压缩文件；在文档中明确 CDN 来源与 MIT 许可证。若验收明确要求离线运行，再单独本地化同版本文件，不同时维护两个来源。

- [ ] **Step 4: 实现导航 partial 与脚本**

导航包含站点名、首页、全部文章、搜索和 staff-only 后台入口。移动按钮使用内联 SVG、`aria-expanded`、`aria-controls`：

```javascript
(() => {
  "use strict";
  const toggle = document.querySelector("[data-nav-toggle]");
  const menu = document.querySelector("[data-nav-menu]");
  if (!toggle || !menu) return;

  toggle.addEventListener("click", () => {
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", String(!expanded));
    toggle.setAttribute("aria-label", expanded ? "展开菜单" : "收起菜单");
    menu.classList.toggle("is-open", !expanded);
  });
})();
```

- [ ] **Step 5: 实现消息和分页 partial**

消息使用 Django `message.tags` 映射状态类。分页必须保留：

```django
href="?page={{ num }}{% if request_query %}&{{ request_query }}{% endif %}"
```

并保留可见文案：

```django
<p class="pagination-info">
  共 {{ page_obj.paginator.num_pages }} 页 · 第 {{ page_obj.number }} 页
</p>
```

- [ ] **Step 6: 建立全局 CSS 基础**

`custom.css` 使用令牌完成正文、容器、导航、skip link、按钮、字段、消息、分页、焦点、移动菜单和减少动态规则。不得新增原始十六进制颜色。

- [ ] **Step 7: 验证页面壳**

```powershell
node --check static/js/main.js
python manage.py test content.tests.test_templates_frontend.ShellAccessibilityTests -v 2
python manage.py test content.tests.test_views.BrowseViewTests -v 1
```

Expected: 全部通过；脚本语法无输出且退出码为 0。

---

### Task 4: 精修首页内容引导

**Files:**
- Modify: `cms_site/templates/content/index.html`
- Modify: `cms_site/static/css/custom.css`
- Test: `cms_site/content/tests/test_templates_frontend.py`

**Interfaces:**
- Consumes: `categories`、`cat.item_count`、`latest_items`。
- Produces: 欢迎区、两个主入口、栏目入口、最新文章和两类空状态。

- [ ] **Step 1: 编写失败测试**

```python
from django.test import TestCase
from django.urls import reverse

from content.models import Category
from content.tests.test_views import BaseViewTests


class HomepagePresentationTests(BaseViewTests):
    def test_homepage_has_primary_guidance(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, "浏览栏目或查找文章")
        self.assertContains(response, "浏览全部文章")
        self.assertContains(response, "搜索文章")

    def test_category_link_contains_count(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, f"?category={self.cat_python.pk}")
        self.assertContains(response, "篇文章")


class HomepageEmptyStateTests(TestCase):
    def test_no_categories_has_recovery_copy(self):
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, "还没有创建栏目")

    def test_no_published_items_has_explanation(self):
        Category.objects.create(name="空栏目")
        response = self.client.get(reverse("content:index"))
        self.assertContains(response, "还没有已发布文章")
```

- [ ] **Step 2: 验证测试先失败**

```powershell
python manage.py test content.tests.test_templates_frontend.HomepagePresentationTests content.tests.test_templates_frontend.HomepageEmptyStateTests -v 2
```

Expected: FAIL，旧首页没有欢迎引导和区分后的空状态。

- [ ] **Step 3: 重写首页语义结构**

使用 `section` 和标题关联。整个栏目入口为一个链接，显示栏目名、可选简介和文章数；最新文章使用 `ul.article-list`，保留标题、栏目和日期。不得加入营销 Hero 或装饰图形。

- [ ] **Step 4: 完成响应式样式**

栏目网格在 375px 单列、768px 两列、1280px 允许三列；文章行在窄屏将元数据换至下一行。卡片半径不超过 `--cms-radius-lg`，不添加多层阴影。

- [ ] **Step 5: 验证首页及既有功能**

```powershell
python manage.py test content.tests.test_templates_frontend.HomepagePresentationTests content.tests.test_templates_frontend.HomepageEmptyStateTests -v 2
python manage.py test content.tests.test_views.BrowseViewTests -v 1
```

Expected: 全部通过；现有栏目名和最新文章断言仍通过。

---

### Task 5: 精修列表、搜索表单与分页

**Files:**
- Modify: `cms_site/templates/content/item_list.html`
- Modify: `cms_site/templates/content/search_form.html`
- Modify: `cms_site/static/css/custom.css`
- Test: `cms_site/content/tests/test_templates_frontend.py`

**Interfaces:**
- Consumes: `form`、`page_obj`、`request_query`、`current_category`。
- Produces: 查询面板、条件摘要、结果数量、文章列表、空状态和恢复路径。

- [ ] **Step 1: 编写失败测试**

```python
class SearchPresentationTests(BaseViewTests):
    def test_search_has_help_and_clear_action(self):
        response = self.client.get(reverse("content:search"))
        self.assertContains(response, "格式：YYYY-MM-DD")
        self.assertContains(response, "清除条件")
        self.assertContains(response, 'for="id_q"')

    def test_active_conditions_are_summarized(self):
        response = self.client.get(
            reverse("content:search"), {"q": "Python"}
        )
        self.assertContains(response, "当前条件")
        self.assertContains(response, "题目关键词：Python")

    def test_empty_result_has_two_recovery_paths(self):
        response = self.client.get(
            reverse("content:search"), {"q": "不存在的关键词xyz"}
        )
        self.assertContains(response, "没有找到相关文章")
        self.assertContains(response, "清除条件")
        self.assertContains(response, "查看全部文章")

    def test_category_list_shows_context(self):
        response = self.client.get(
            reverse("content:item_list"), {"category": self.cat_python.pk}
        )
        self.assertContains(response, "栏目：教学动态")
```

- [ ] **Step 2: 运行红灯测试**

```powershell
python manage.py test content.tests.test_templates_frontend.SearchPresentationTests -v 2
```

Expected: FAIL，旧模板没有条件摘要、清除入口或帮助说明。

- [ ] **Step 3: 重写查询表单**

每个字段使用显式标签。起止日期增加对应帮助文本；字段错误用 `role="alert"` 并紧邻字段；非字段错误提供摘要。保留 `{{ form.q }}`、`{{ form.start }}`、`{{ form.end }}`、`{{ form.category }}`，不得自行解析参数。

```django
<div class="field-group">
  <label for="id_start">起始日期</label>
  {{ form.start }}
  <p id="start-help" class="field-help">格式：YYYY-MM-DD</p>
  {% if form.start.errors %}
  <div class="field-errors" role="alert">{{ form.start.errors }}</div>
  {% endif %}
</div>
```

- [ ] **Step 4: 重写结果布局**

桌面采用查询侧栏加结果主体；移动端查询表单位于结果前。页面标题区显示栏目语境和结果数。合法表单通过 `form.cleaned_data` 输出只读条件摘要；非法表单显示“查询条件有误，请修正后重新查询”。

- [ ] **Step 5: 接入统一分页**

删除模板内重复分页代码，改为：

```django
{% include "partials/pagination.html" %}
```

不得改变 `request_query` 拼接方式。

- [ ] **Step 6: 验证搜索行为与安全契约**

```powershell
python manage.py test content.tests.test_templates_frontend.SearchPresentationTests -v 2
python manage.py test content.tests.test_views.SearchViewTests content.tests.test_views.PaginationTests -v 2
python manage.py test content.tests.test_forms -v 1
python manage.py test content.tests.test_security -v 1
```

Expected: 全部通过；非法日期仍显示原文；分页仍保留查询参数；XSS 测试不回归。

---

### Task 6: 精修文章详情阅读体验

**Files:**
- Modify: `cms_site/templates/content/item_detail.html`
- Modify: `cms_site/static/css/custom.css`
- Test: `cms_site/content/tests/test_templates_frontend.py`

**Interfaces:**
- Consumes: `item.title`、`item.category`、`item.publish_time`、`item.author`、自动转义的 `item.content`。
- Produces: 面包屑、窄阅读栏、元数据组与返回栏目路径。

- [ ] **Step 1: 编写失败测试**

```python
class ArticleDetailPresentationTests(BaseViewTests):
    def test_detail_has_breadcrumb_and_return_path(self):
        response = self.client.get(
            reverse("content:item_detail", args=[self.item1.pk])
        )
        self.assertContains(response, 'aria-label="面包屑"')
        self.assertContains(response, "返回该栏目")

    def test_detail_uses_article_landmark(self):
        response = self.client.get(
            reverse("content:item_detail", args=[self.item1.pk])
        )
        self.assertContains(response, "<article")
        self.assertContains(response, 'class="article-content"')
```

- [ ] **Step 2: 验证先失败**

```powershell
python manage.py test content.tests.test_templates_frontend.ArticleDetailPresentationTests -v 2
```

Expected: FAIL，旧模板没有新的语义类与完整可访问名称。

- [ ] **Step 3: 实现阅读布局**

将文章主体限制到 `--cms-read-max`，标题允许自然换行，元数据使用 `dl` 或语义清晰的组合。正文继续使用 Django 自动转义与 `linebreaksbr`，禁止 `safe`。

- [ ] **Step 4: 验证详情与草稿隔离**

```powershell
python manage.py test content.tests.test_templates_frontend.ArticleDetailPresentationTests -v 2
python manage.py test content.tests.test_views.BrowseViewTests -v 1
python manage.py test content.tests.test_security -v 1
```

Expected: 全部通过；草稿详情仍为 404；脚本内容仍被转义。

---

### Task 7: 美化原生 Django Admin

**Files:**
- Create: `cms_site/templates/admin/base_site.html`
- Create: `cms_site/static/css/admin.css`
- Create: `cms_site/content/tests/test_templates_admin.py`

**Interfaces:**
- Consumes: Django 5.2 Admin 模板块、现有 `CategoryAdmin`、`ItemAdmin` 和站点标题。
- Produces: 覆盖全部 Admin 页面的额外样式，不改变表单字段或动作。

- [ ] **Step 1: 编写失败测试**

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase


class AdminTemplatePresentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="admin-ui", password="pass12345", is_staff=True
        )
        permissions = Permission.objects.filter(content_type__app_label="content")
        cls.user.user_permissions.add(*permissions)

    def setUp(self):
        self.client.force_login(self.user)

    def test_admin_index_loads_project_stylesheet(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "css/admin.css")

    def test_admin_item_list_keeps_native_actions(self):
        response = self.client.get("/admin/content/item/")
        self.assertContains(response, "设为已发布")
        self.assertContains(response, "设为草稿")

    def test_admin_add_page_keeps_required_fields(self):
        response = self.client.get("/admin/content/item/add/")
        self.assertContains(response, "标题")
        self.assertContains(response, "所属栏目")
        self.assertContains(response, "发布状态")
```

- [ ] **Step 2: 验证样式测试先失败**

```powershell
python manage.py test content.tests.test_templates_admin.AdminTemplatePresentationTests -v 2
```

Expected: `css/admin.css` 断言失败；原生字段与动作断言通过，证明行为基线存在。

- [ ] **Step 3: 添加官方模板覆盖**

`base_site.html` 继承 `admin/base.html`，加载静态资源并保留原生块：

```django
{% extends "admin/base.html" %}
{% load static %}

{% block extrastyle %}
{{ block.super }}
<link rel="stylesheet" href="{% static 'css/tokens.css' %}">
<link rel="stylesheet" href="{% static 'css/admin.css' %}">
{% endblock %}

{% block branding %}
<div id="site-name"><a href="{% url 'admin:index' %}">CMS 内容管理</a></div>
{% endblock %}
```

- [ ] **Step 4: 编写 Admin CSS**

覆盖 `body`、`#header`、breadcrumbs、module、table、form-row、input/select/textarea、submit-row、button、messagelist、object-tools、selector、pagination 和删除确认。使用 `--cms-*` 令牌；主操作蓝、危险操作红、消息具备文字与边框；不隐藏任何原生控件。

- [ ] **Step 5: 验证 Admin 行为无回归**

```powershell
python manage.py test content.tests.test_templates_admin -v 2
python manage.py test content.tests.test_admin -v 2
```

Expected: 新样式断言和现有登录、CRUD、删除保护、批量发布/撤回全部通过。

---

### Task 8: 建立组件状态夹具并检查设计系统合规

**Files:**
- Create: `cms_site/templates/content/_showcase.html`
- Modify: `cms_site/content/tests/test_templates_frontend.py`
- Modify: `DESIGN.md` only if implementation产生新的复用模式或明确债务。

**Interfaces:**
- Produces: 无公开 URL 的模板夹具，覆盖主要组件状态。
- Consumes: 所有前台 partial 与 CSS 类。

- [ ] **Step 1: 编写失败的夹具测试**

```python
from django.template.loader import render_to_string


class ComponentShowcaseTests(TestCase):
    def test_showcase_renders_required_states(self):
        html = render_to_string("content/_showcase.html")
        for marker in (
            "state-default",
            "state-hover",
            "state-focus",
            "state-disabled",
            "state-error",
            "state-empty",
        ):
            self.assertIn(marker, html)
```

- [ ] **Step 2: 验证模板不存在**

```powershell
python manage.py test content.tests.test_templates_frontend.ComponentShowcaseTests -v 2
```

Expected: FAIL with `TemplateDoesNotExist`。

- [ ] **Step 3: 创建状态夹具**

夹具呈现按钮、链接、字段、字段错误、消息、栏目入口、文章行、分页和空状态。通过状态类展示不可直接伪造的 hover/focus 参考，但不增加 URL 或业务视图。

- [ ] **Step 4: 扫描设计令牌违规**

```powershell
rg -n "#[0-9a-fA-F]{3,8}|rgb\(|hsl\(" cms_site/static/css
rg -n "font-size:|margin:|padding:|gap:" cms_site/static/css
```

Expected: `tokens.css` 中允许出现颜色定义；`custom.css` 与 `admin.css` 不包含孤立颜色，字号和间距均引用令牌或必要的 CSS 布局机制。

- [ ] **Step 5: 运行模板测试**

```powershell
python manage.py test content.tests.test_templates_frontend content.tests.test_templates_admin -v 2
```

Expected: 全部通过。

---

### Task 9: 同步课程设计、操作、测试与 AI 文档

**Files:**
- Modify: `docs/02_详细设计文档.md`
- Modify: `docs/05_测试报告.md`
- Modify: `docs/07_AI使用说明.md`
- Modify: `docs/09_操作说明书.md`

**Interfaces:**
- Consumes: 最终实现、测试数量和视觉 QA 证据。
- Produces: 可解释、可复现、过程透明的课程文档链。

- [ ] **Step 1: 更新详细设计文档**

补充：`DESIGN.md` 令牌合同、Django 模板 partial、移动导航原生脚本、Admin 官方模板覆盖、未改变模型/查询/Admin CRUD 的取舍说明。

- [ ] **Step 2: 更新操作说明书**

同步新的前台欢迎入口、活动导航、查询条件摘要、清除条件、空状态恢复路径和后台视觉变化。操作步骤仍对应现有 URL 和功能。

- [ ] **Step 3: 更新 AI 使用说明**

记录使用的模型/工具、UI 需求拆解、设计规格、代码探索、计划、实施、测试和视觉 QA 环节；说明采纳设计系统与原生 Admin 覆盖、拒绝自建后台和大型前端框架的理由；声明未上传敏感数据。

- [ ] **Step 4: 回填测试报告**

仅在 Task 10 的命令实际运行后填写真实测试数量、结果、浏览器宽度、发现的问题和修复。不得预填“通过”。

- [ ] **Step 5: 文档一致性检查**

```powershell
rg -n "React|Vue|自建后台" docs DESIGN.md
rg -n "按题目|按发表时间|按栏目|Category|Item|Django Admin" docs/02_详细设计文档.md docs/09_操作说明书.md
```

Expected: 若提及 React/Vue/自建后台，只能作为明确拒绝的取舍；三种查询和两个实体均有对应说明。

---

### Task 10: 完整自动化与真实浏览器验收

**Files:**
- Verify all changed files.
- Modify only files required to fix failures caused by this implementation.

**Interfaces:**
- Produces: 自动化测试、静态检查、浏览器截图、交互证据和最终审查结论。

- [ ] **Step 1: 运行 Python 与 Django 质量门**

Run from `cms_site`:

```powershell
ruff check .
python manage.py test -v 2
python manage.py check --deploy
```

Expected: Ruff 和测试退出码 0；`check --deploy` 可能报告现有开发配置警告，逐条记录，不通过修改与 UI 无关的生产配置来掩盖。

- [ ] **Step 2: 启动服务并验证核心任务**

```powershell
python manage.py runserver 127.0.0.1:8000
```

若端口已占用则使用 `8001`。实际操作：首页进入栏目、全部文章、搜索和详情；分别执行题目、时间、栏目、组合查询；验证非法日期、空结果、分页保留条件；以 staff 账号完成 Admin 登录、Item 新增/修改/删除、Category 管理和发布状态切换；确认草稿前台不可见。

- [ ] **Step 3: 执行 Playwright 浏览器检查**

加载 `playwright` 技能，用真实 Chromium 在 `375x812`、`768x1024`、`1280x800` 检查：首页、列表、搜索合法/错误/空状态、详情、Admin 登录、Admin 首页、Item 列表和 Item 表单。

每个断点至少断言：

```text
document.documentElement.scrollWidth === document.documentElement.clientWidth
移动菜单可展开并更新 aria-expanded
Tab 可聚焦 skip link、导航、查询字段、按钮和分页
长标题/栏目名不裁切且不覆盖相邻内容
错误、选中和危险状态不只依赖颜色
```

- [ ] **Step 4: 执行 `/visual-qa`**

使用 fresh screenshots 覆盖三个断点和关键交互状态。修复所有 Critical/Major 视觉、可访问性、认知流程问题后重新截图，直至双评审门通过。记录截图与报告路径。

- [ ] **Step 5: 执行 Lighthouse 真实浏览器审计**

在真实 Chrome 的移动与桌面预设下运行 3 次并取中位数。报告 Performance、Accessibility、Best Practices、SEO；若未达到规则要求的 100，不得宣称该门通过，应继续定位具体审计项或明确阻塞原因。不得通过删除交互或隐藏内容换分。

- [ ] **Step 6: 执行实现后审查**

调用 `godot-code-review` 不适用，因为项目不是 Godot。对重大前端实现调用 `/review-work`，输入批准规格、`DESIGN.md`、测试输出、视觉 QA 证据、Lighthouse 结果和剩余债务。修复由本次改造引入的问题后重跑相关门。

- [ ] **Step 7: 最终核对原始题目**

逐项确认：Python/Django、Category/Item、管理 CRUD、发布与栏目选择、普通浏览、三种查询、PEP 8、Git 历史未被破坏、AI 说明、测试、校验、部署、演示数据和清晰目录全部仍满足。将真实结果回填 `docs/05_测试报告.md`。

## Commit Strategy

默认不提交。只有用户明确要求提交后，才按下列原子边界分别暂存指定文件：

1. `DESIGN.md` + `tokens.css`。
2. 模板上下文测试 + `views.py`。
3. 全局壳、partials、`main.js`、`custom.css`。
4. 首页模板与测试。
5. 列表/搜索/详情模板与测试。
6. Admin 模板、CSS 与测试。
7. 文档更新。

每次提交前运行 `git status --short` 和 `git diff -- <明确文件列表>`；禁止 `git add .`、`git add -A`、amend 或处理用户已有的无关修改。

## Completion Checklist

- [ ] `DESIGN.md` 八节和 Research Log 完整，令牌与 CSS 一致。
- [ ] 前台所有复用模式具有必需状态和语义。
- [ ] 原生 Admin 行为未替换，CRUD/权限/批量动作测试通过。
- [ ] 三种查询、组合查询、分页和草稿隔离无回归。
- [ ] `ruff check .` 和 `python manage.py test -v 2` 通过。
- [ ] 375、768、1280px 的前台与 Admin 视觉/交互证据齐全。
- [ ] 键盘、焦点、减少动态、长文本、空状态和错误状态均验证。
- [ ] Lighthouse 结果如实记录，未通过的门明确标记而非宣称完成。
- [ ] 课程设计、测试、操作和 AI 文档与实现同步。
- [ ] `/visual-qa` 与 `/review-work` 最终门通过或明确列出阻塞项。
