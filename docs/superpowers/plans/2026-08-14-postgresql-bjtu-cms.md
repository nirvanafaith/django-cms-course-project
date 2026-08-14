# PostgreSQL 18 与北交大风格 CMS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 Django CMS 完整改造成 PostgreSQL 18.6 单数据库、两级用户权限、可审计后台、北交大主站风格前台，并提供可复现数据、测试和课程交付材料。

**Architecture:** 保持 Django 服务端渲染单体架构。`content` 负责栏目、文章与公开查询，Django `auth`/Admin 负责用户和后台 CRUD，`core` 负责 PostgreSQL/Redis 健康、结构化日志和后台日志查看；Docker Compose 是标准运行与测试入口。

**Tech Stack:** Python 3.12、Django 5.2.17、PostgreSQL 18.6、Psycopg 3.3.4、Redis 7.4、Waitress 3.0.2、WhiteNoise 6.12.0、Ruff 0.16.3、coverage.py 7.15.4、Django Templates、原生 CSS/JavaScript、Playwright。

## Global Constraints

- 只在主对话执行，不调用 subagent。
- 三张核心表固定为 `auth_user`、`content_category`、`content_item`；Django 支撑表保留。
- 所有运行和测试路径只允许 PostgreSQL 18.6；删除 MySQL、PyMySQL 和 SQLite 分支。
- 普通用户为 `is_staff=False/is_superuser=False`；管理员为 `is_staff=True/is_superuser=True`。
- 匿名浏览开放，普通用户可登录但不可注册；只有超级用户显示并进入后台。
- 请求/安全日志使用本地 UTF-8 JSON Lines，按天轮转保留 14 天；不建立请求日志数据表。
- 官网素材来自 `https://www.bjtu.edu.cn/`，本地化保存并记录来源、日期、用途和许可说明。
- 当前工作区已有用户修改：`content/forms.py` 的 366 天范围校验、`content/selectors.py` 的稳定排序、`custom.css` 的错误页样式、UTF-8 `启动系统.bat` 必须保留并合并。
- 当前工作区已删除旧 `content/tests/`、旧交付文档和 `ruff.toml`；不得通过 `git restore` 恢复。新测试写到 `cms_site/tests/`，新缺失文档使用新文件名。
- `.gitignore` 的现有用户修改不回退；测试结束后清理本轮产生的 `.coverage`、`htmlcov/`、`.pytest_cache/`。
- 每次提交前使用显式路径暂存，并运行 `git diff --staged --name-status`，不得夹带其他工作区变更。
- 每个 Python 任务完成后对全部变更 Python 文件运行 BasedPyright LSP diagnostics。
- 每个编程任务都使用 Context7 核对对应 Django/PostgreSQL API；禁止 `as any`、忽略类型错误、空 `catch`、吞异常或删除失败测试。
- 所有提交使用仓库既有的中文 Conventional Commits 风格。

---

### Task 1: PostgreSQL-only Django database backend

**Files:**
- Create: `cms_site/tests/__init__.py`
- Create: `cms_site/tests/test_database_config.py`
- Create: `cms_site/pyproject.toml`
- Modify: `cms_site/config/backends.py`
- Modify: `cms_site/config/settings.py`
- Modify: `cms_site/requirements.txt`

**Interfaces:**
- Produces: `build_databases(mode: str) -> BackendSettings` using only `django.db.backends.postgresql`.
- Consumes environment: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`.
- Later tasks rely on Psycopg 3.3.4 and PostgreSQL-specific migrations.

- [ ] **Step 1: Write failing database configuration tests**

```python
# cms_site/tests/test_database_config.py
import os
from unittest.mock import patch

from django.test import SimpleTestCase

from config.backends import build_databases
from config.env import ConfigError


class PostgreSQLSettingsTests(SimpleTestCase):
    def test_builds_only_postgresql_backend(self) -> None:
        values = {
            "POSTGRES_DB": "cms",
            "POSTGRES_USER": "cms_user",
            "POSTGRES_PASSWORD": "secret",
            "POSTGRES_HOST": "db",
            "POSTGRES_PORT": "5432",
        }
        with patch.dict(os.environ, values, clear=True):
            database = build_databases("local")["default"]

        self.assertEqual(database["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(database["NAME"], "cms")
        self.assertEqual(database["PORT"], "5432")
        self.assertEqual(database["CONN_MAX_AGE"], 60)
        self.assertTrue(database["CONN_HEALTH_CHECKS"])
        self.assertEqual(database["OPTIONS"], {"connect_timeout": 5})

    def test_requires_postgresql_password(self) -> None:
        values = {
            "POSTGRES_DB": "cms",
            "POSTGRES_USER": "cms_user",
            "POSTGRES_HOST": "db",
            "POSTGRES_PORT": "5432",
        }
        with patch.dict(os.environ, values, clear=True), self.assertRaises(ConfigError):
            build_databases("local")
```

- [ ] **Step 2: Run tests and confirm the MySQL/SQLite implementation fails**

Run from `cms_site`:

```powershell
$env:POSTGRES_DB='cms'; $env:POSTGRES_USER='cms_user'; $env:POSTGRES_PASSWORD='test-secret'; $env:POSTGRES_HOST='127.0.0.1'; $env:POSTGRES_PORT='5432'; .\.venv\Scripts\python.exe manage.py test tests.test_database_config -v 2
```

Expected: FAIL because `build_databases()` still reads `DB_ENGINE` and returns MySQL or SQLite settings.

- [ ] **Step 3: Pin PostgreSQL and quality dependencies**

`requirements.txt` must contain exactly pinned runtime/tool dependencies, replacing `PyMySQL==1.1.1` with:

```text
psycopg[binary]==3.3.4
ruff==0.16.3
coverage==7.15.4
```

Preserve the existing exact pins for Django, Redis, Waitress, WhiteNoise, asgiref, sqlparse, and tzdata.

- [ ] **Step 4: Implement PostgreSQL-only settings**

Replace `build_databases()` with a single PostgreSQL mapping:

```python
def build_databases(_mode: str) -> BackendSettings:
    """构建唯一受支持的 PostgreSQL 数据库连接。"""
    return {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env.require_env("POSTGRES_DB"),
            "USER": env.require_env("POSTGRES_USER"),
            "PASSWORD": env.require_env("POSTGRES_PASSWORD"),
            "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {"connect_timeout": 5},
        }
    }
```

Remove `Path`, `ImproperlyConfigured`, `pymysql`, `DB_ENGINE`, `DB_*`, SQLite and MySQL branches. Add `"django.contrib.postgres"` to `INSTALLED_APPS`. Do not add fallback defaults for credentials.

- [ ] **Step 5: Add project-level Ruff and coverage configuration**

Create `cms_site/pyproject.toml` with Python 3.12 target, 100-character line limit, Ruff `E/F/I/B/UP/RUF/DJ` rules, and coverage source restricted to `config`, `content`, and `core`; omit migrations and tests from coverage.

- [ ] **Step 6: Install, diagnose, and test**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py test tests.test_database_config -v 2
.\.venv\Scripts\ruff.exe check config/backends.py config/settings.py tests/test_database_config.py
```

Expected: all commands exit 0. Run LSP diagnostics on `config/backends.py`, `config/settings.py`, and `tests/test_database_config.py`.

- [ ] **Step 7: Commit only Task 1 paths**

```powershell
$env:GIT_MASTER='1'; git add cms_site/requirements.txt cms_site/pyproject.toml cms_site/config/backends.py cms_site/config/settings.py cms_site/tests/__init__.py cms_site/tests/test_database_config.py
$env:GIT_MASTER='1'; git diff --staged --name-status
$env:GIT_MASTER='1'; git commit -m "feat: 全面切换 PostgreSQL 数据库后端"
```

### Task 2: PostgreSQL 18.6 runtime, Compose, and Windows launchers

**Files:**
- Create: `cms_site/tests/test_runtime_config.py`
- Create: `cms_site/core/management/commands/verify_postgres.py`
- Create: `cms_site/core/tests/test_verify_postgres.py`
- Modify: `compose.yaml`
- Modify: `.env.example`
- Modify: `cms_site/Dockerfile`
- Modify: `cms_site/core/management/commands/preflight.py`
- Modify: `启动系统.bat`
- Modify: `启动公网系统.bat` (merge the existing untracked file)

**Interfaces:**
- Produces Compose services `db`, `redis`, `migrate`, `web`, `test`.
- Produces command `python manage.py verify_postgres` that rejects non-PostgreSQL or server major versions below 18.

- [ ] **Step 1: Write failing runtime-file and PostgreSQL verification tests**

```python
# cms_site/tests/test_runtime_config.py
from pathlib import Path
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[2]


class RuntimeConfigTests(SimpleTestCase):
    def test_compose_uses_postgresql_18_only(self) -> None:
        text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("postgres:18.6-bookworm", text)
        self.assertIn("POSTGRES_DB", text)
        self.assertNotIn("mysql", text.casefold())
        self.assertNotIn("DB_ENGINE", text)

    def test_requirements_remove_mysql_driver(self) -> None:
        text = (ROOT / "cms_site" / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotIn("PyMySQL", text)
        self.assertIn("psycopg[binary]==3.3.4", text)
```

`test_verify_postgres.py` must patch `connection.vendor` and cursor results to prove PostgreSQL 18 passes and PostgreSQL 17/non-PostgreSQL raise `CommandError`.

- [ ] **Step 2: Confirm tests fail against MySQL Compose**

Run `manage.py test tests.test_runtime_config core.tests.test_verify_postgres -v 2`; expected FAIL for MySQL image and missing command.

- [ ] **Step 3: Replace Compose infrastructure**

Use `postgres:18.6-bookworm`, `pg_isready`, port `5432`, named volume `postgres-data`, UTF-8/C locale, and these app variables:

```yaml
POSTGRES_DB: ${POSTGRES_DB:-cms}
POSTGRES_USER: ${POSTGRES_USER:-cms_user}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env}
POSTGRES_HOST: db
POSTGRES_PORT: "5432"
DEMO_USER_PASSWORD: ${DEMO_USER_PASSWORD:?Set DEMO_USER_PASSWORD in .env}
DEMO_ADMIN_PASSWORD: ${DEMO_ADMIN_PASSWORD:?Set DEMO_ADMIN_PASSWORD in .env}
```

`migrate` runs `migrate --noinput`, `verify_postgres`, `seed_data`, and `collectstatic --noinput`. `test` runs `coverage run manage.py test --exclude-tag=postgres_performance` followed by `coverage report --fail-under=80` in the same container process. Mount `app-logs:/app/logs` for `web` and `migrate`. Keep Redis internal and Web bound to `127.0.0.1`.

- [ ] **Step 4: Update Dockerfile and launchers**

Create `/app/logs`, give UID 10001 ownership, and provide dummy PostgreSQL variables only for build-time `collectstatic`; do not connect during build. Rewrite `启动系统.bat` to check Docker, run `docker compose up --build --wait`, print front/admin URLs, and open the front page. Preserve UTF-8 code page and strict `errorlevel` handling. Update the public BAT to use `POSTGRES_*` names and never store credentials.

- [ ] **Step 5: Implement `verify_postgres` and update preflight wording**

The command queries `SHOW server_version_num`, verifies `connection.vendor == "postgresql"`, requires `int(version_num) >= 180000`, and prints the server version. Replace “检查 MySQL” messages with PostgreSQL wording.

- [ ] **Step 6: Validate runtime files**

```powershell
docker compose config
docker compose build
.\.venv\Scripts\python.exe manage.py test tests.test_runtime_config core.tests.test_verify_postgres -v 2
```

Expected: config/build/tests exit 0. Run LSP diagnostics on the new command and tests.

- [ ] **Step 7: Commit Task 2 explicitly**

Commit message: `build: 接入 PostgreSQL 18.6 容器运行链路`.

### Task 3: PostgreSQL schema constraints, draft default, and indexes

**Files:**
- Create: `cms_site/tests/test_postgresql_models.py`
- Create: `cms_site/content/migrations/0002_postgresql_constraints_indexes.py`
- Modify: `cms_site/content/models.py`

**Interfaces:**
- Produces `Item` with required content, `is_published=False`, stable ordering, and three PostgreSQL indexes.
- Produces `pg_trgm` extension through migration.

- [ ] **Step 1: Write failing model metadata and behavior tests**

Test that new `Item` defaults to draft, blank content fails `full_clean()`, ordering is `['-publish_time', '-pk']`, index names are `item_pub_time_idx`, `item_cat_pub_time_idx`, `item_title_trgm_idx`, category deletion raises `ProtectedError`, and deleting an author sets `author_id` to `None`.

- [ ] **Step 2: Run the tests and confirm current defaults fail**

Run `docker compose run --rm test python manage.py test tests.test_postgresql_models -v 2`; expected failures for blank content, published default, ordering, and indexes.

- [ ] **Step 3: Implement the model contract**

```python
from django.contrib.postgres.indexes import GinIndex

content = models.TextField("正文")
is_published = models.BooleanField("发布状态", default=False)

class Meta:
    ordering = ["-publish_time", "-pk"]
    indexes = [
        models.Index(fields=["is_published", "-publish_time"], name="item_pub_time_idx"),
        models.Index(
            fields=["category", "is_published", "-publish_time"],
            name="item_cat_pub_time_idx",
        ),
        GinIndex(fields=["title"], name="item_title_trgm_idx", opclasses=["gin_trgm_ops"]),
    ]
```

- [ ] **Step 4: Generate and inspect migration**

Run `manage.py makemigrations content`; ensure the migration includes `TrigramExtension()`, field alterations, ordering, and all three indexes. Rename the generated file to the exact path above without editing unrelated migrations.

- [ ] **Step 5: Apply and verify PostgreSQL objects**

Run migrations on the validation Compose project, then query `pg_extension` and `pg_indexes` to assert `pg_trgm` and all named indexes exist. Run LSP, Ruff, and model tests.

- [ ] **Step 6: Commit**

Commit message: `feat: 强化文章约束与 PostgreSQL 查询索引`.

### Task 4: Public authentication and role-aware navigation

**Files:**
- Create: `cms_site/templates/registration/login.html`
- Create: `cms_site/tests/test_authentication.py`
- Modify: `cms_site/config/urls.py`
- Modify: `cms_site/config/settings.py`
- Modify: `cms_site/templates/partials/nav.html`

**Interfaces:**
- Produces named routes `login` at `/accounts/login/` and `logout` at `/accounts/logout/`.
- Navigation uses `user.is_superuser`, never `user.is_staff`, for the management entry.

- [ ] **Step 1: Write failing anonymous/normal/admin flow tests**

Create a normal user and superuser. Assert login succeeds for both, the normal user never sees “管理后台”, the superuser does, POST logout ends the session, and GET `/admin/` redirects normal users to Admin login.

- [ ] **Step 2: Confirm missing public login routes fail**

Run `manage.py test tests.test_authentication -v 2`; expected FAIL on `reverse('login')`.

- [ ] **Step 3: Add Django auth routes and redirects**

Use Django `LoginView` with `registration/login.html` and `LogoutView`; set `LOGIN_REDIRECT_URL = '/'` and `LOGOUT_REDIRECT_URL = '/'`. Logout must be a POST form with CSRF token.

- [ ] **Step 4: Replace navigation shell behavior**

Keep the existing skip link and mobile toggle. Add login/logout state, use `user.is_superuser` for the Admin link, and retain the existing stable page-current semantics.

- [ ] **Step 5: Diagnose, test, and commit**

Run LSP on URL/settings/test files, Ruff, and authentication tests. Commit message: `feat: 增加普通用户登录与管理员导航入口`.

### Task 5: User roles, content validation, and audit Admin

**Files:**
- Create: `cms_site/core/admin_forms.py`
- Create: `cms_site/core/admin.py`
- Create: `cms_site/content/admin_forms.py`
- Create: `cms_site/tests/test_admin_management.py`
- Modify: `cms_site/content/admin.py`

**Interfaces:**
- Produces `CmsUserCreationForm`, `CmsUserChangeForm`, and visible `role` choices `normal/admin`.
- Produces read-only `LogEntryAdmin`.
- Produces `ItemAdminForm.clean_title()` and `.clean_content()` that reject whitespace-only values.

- [ ] **Step 1: Write failing Admin integration tests**

Cover user creation, role promotion/demotion synchronizing both flags, disabled users, whitespace-only article validation, Category article-count query count, batch publish/draft actions, and `LogEntry` generation. Assert audit records cannot be added, changed, or deleted from Admin.

- [ ] **Step 2: Confirm the default UserAdmin and current ItemAdmin fail**

Run `manage.py test tests.test_admin_management -v 2`; expected failures for missing role abstraction, blank content, and direct audit list.

- [ ] **Step 3: Implement role forms without a new database field**

`role` is a `ChoiceField` with `normal/admin`. `save()` sets both flags from the selected value. Re-register Django `User` using a custom `UserAdmin`; hide groups/user-permission fields because every visible administrator is a superuser.

- [ ] **Step 4: Register read-only management audit logs**

Register `django.contrib.admin.models.LogEntry` with list columns action time, user, action flag, content type, and object representation; add user/action/content-type/date filters and object/user search. All mutation permission methods return `False`.

- [ ] **Step 5: Harden content Admin forms and actions**

Attach `ItemAdminForm`, include author in fields/list, preserve existing aggregation and transaction-on-commit cache invalidation, and explicitly call `log_change()` for each item affected by custom bulk actions.

- [ ] **Step 6: Validate and commit**

Run LSP on all changed Python files, Ruff, and Admin tests. Commit message: `feat: 完善用户角色与内容审计后台`.

### Task 6: Structured, redacted, 14-day application logs

**Files:**
- Create: `cms_site/core/json_logging.py`
- Create: `cms_site/core/tests/test_json_logging.py`
- Modify: `cms_site/core/middleware.py`
- Modify: `cms_site/config/settings.py`
- Modify: `cms_site/Dockerfile`

**Interfaces:**
- Produces `mask_ip(address: str) -> str` and `JsonFormatter`.
- File destination: `settings.LOG_DIR / 'cms.jsonl'`.
- Allowed event fields: timestamp, level, logger, event, request_id, method, path, status, duration_ms, user_id, masked_ip.

- [ ] **Step 1: Write failing formatter, redaction, and middleware tests**

Assert IPv4 becomes `203.0.113.0`, IPv6 retains only the first four hextets, unknown addresses become `unknown`, JSON output excludes query strings/cookies/password/auth headers, and a completed request contains status/duration/request ID/user ID.

- [ ] **Step 2: Confirm current plain-text logging fails**

Run `manage.py test core.tests.test_json_logging -v 2`; expected failure because `JsonFormatter` is missing.

- [ ] **Step 3: Implement JSON logging**

Use a standard-library `logging.Formatter`; serialize only the allowlisted fields with `ensure_ascii=False`. Update request/security logging calls to use `extra={...}` and `request.path`, never `get_full_path()`.

- [ ] **Step 4: Configure rotation and login security events**

Add a console JSON handler and `TimedRotatingFileHandler` with `when='midnight'`, `backupCount=14`, UTF-8, local time. Expand login throttling to both `/accounts/login/` and `/admin/login/`; log failures, blocks and degraded Redis using the same schema.

Define the log directory explicitly in settings:

```python
LOG_DIR = Path(os.environ.get("CMS_LOG_DIR", BASE_DIR / "logs"))
LOG_FILE = LOG_DIR / "cms.jsonl"
```

The container sets `CMS_LOG_DIR=/app/logs`; the image build creates this directory with UID 10001 ownership.

- [ ] **Step 5: Verify and commit**

Run tests, LSP, Ruff, and manually inspect one emitted line with `ConvertFrom-Json`. Commit message: `feat: 接入脱敏结构化请求与安全日志`.

### Task 7: Bounded read-only Admin log viewer

**Files:**
- Create: `cms_site/core/log_reader.py`
- Create: `cms_site/core/forms.py`
- Create: `cms_site/core/admin_views.py`
- Create: `cms_site/templates/admin/system_logs.html`
- Create: `cms_site/core/tests/test_log_viewer.py`
- Modify: `cms_site/config/urls.py`
- Modify: `cms_site/templates/admin/base_site.html`

**Interfaces:**
- Produces `read_log_events(log_dir: Path, *, limit: int = 5000) -> list[dict[str, object]]`.
- Produces `SystemLogFilterForm` fields date, level, event, status, request_id.
- Produces named route `admin_system_logs` at `/admin/system-logs/`.

- [ ] **Step 1: Write failing reader/view permissions tests**

Use temporary JSONL files to test newest-first ordering, current plus rotated files, 5,000-record cap, malformed-line skip, every filter, pagination, missing-file empty state, normal-user denial, and superuser access.

- [ ] **Step 2: Confirm missing service/view fails**

Run `manage.py test core.tests.test_log_viewer -v 2`; expected import/route failures.

- [ ] **Step 3: Implement bounded parser and typed form**

Read only `cms.jsonl` and `cms.jsonl.YYYY-MM-DD` files. Validate decoded values are dictionaries, keep only allowlisted keys, stop at `limit`, and never expose raw lines on parse failure.

- [ ] **Step 4: Implement Admin view and template**

Wrap the view with `admin.site.admin_view`, use `admin.site.each_context(request)`, `Paginator(..., 50)`, preserve filters in pagination, and add a “系统日志” link to `base_site.html`. The template extends Admin styling and is read-only.

- [ ] **Step 5: Verify and commit**

Run LSP/Ruff/tests and manually request the page as normal/admin users. Commit message: `feat: 增加后台系统日志查看入口`.

### Task 8: Idempotent original BJTU-style demo data

**Files:**
- Create: `cms_site/content/demo_data.py`
- Create: `cms_site/tests/test_seed_data.py`
- Modify: `cms_site/content/management/commands/seed_data.py`

**Interfaces:**
- Produces exactly 8 categories, 36 items, 3 drafts, 2 normal users and 2 superusers.
- Consumes `DEMO_USER_PASSWORD` and `DEMO_ADMIN_PASSWORD`; missing either raises `CommandError`.

- [ ] **Step 1: Define the exact article title set in the failing test**

Use these 36 original titles distributed across the eight approved categories:

```text
交通强国建设专题研讨会在校举行
学校召开新学期重点工作部署会
轨道交通自主创新成果集中发布
知行育人计划启动仪式顺利举行
校园开放日展示学科建设新进展
关于秋季学期开学安排的通知
图书馆暑期开放时间调整公告
校园网络维护与服务暂停通知
研究生奖学金材料提交提醒
实验室安全检查工作通知
智能交通课程群完成教学改革验收
本科生科研训练项目开始申报
计算机基础课程开放实践周报名
教师教学能力提升工作坊举行
跨学科培养方案发布试行
校园文化节系列活动正式启动
学生创新创业成果展开幕
志愿服务项目交流会圆满结束
秋季运动会报名通道开放
社团招新服务周安排发布
本科招生线上咨询活动启动
研究生招生政策宣讲会预告
毕业生校园双选会参会指南
国际学生入学服务手册发布
轨道交通前沿学术论坛预告
人工智能与工程教育讲座举行
青年学者交叉论坛征集报告
城市交通治理专题报告会开放预约
国际合作伙伴周活动日程发布
海外交流项目线上说明会举行
留学生文化交流活动报名开始
联合培养项目申请指南更新
年度信息公开报告正式发布
校级规章制度目录完成更新
公共服务事项办事指南发布
校园数据开放目录新增资源
```

- [ ] **Step 2: Run current seed tests and confirm wrong counts/content fail**

Expected: current command creates 5 categories, 63 synthetic short items, and no users.

- [ ] **Step 3: Implement typed seed specifications and full bodies**

Use frozen dataclasses for categories/articles. Every article body contains three original paragraphs: event/background, concrete arrangements or outcomes, and contact/follow-up information; do not copy official article text. Use fixed aware timestamps spanning 2023-2026.

- [ ] **Step 4: Implement transactional idempotent upserts**

Use `update_or_create()` by username/category name/article title plus category. Synchronize role flags and passwords from environment. Assign authors deterministically to the two admins. Output created/updated/skipped/draft counts.

- [ ] **Step 5: Run seed twice and commit**

Assert counts remain 8/36/4 and exactly 3 drafts after both runs. Run LSP/Ruff. Commit message: `feat: 提供北交大风格可复现演示数据`.

### Task 9: Search validation, stable queries, homepage sections, and performance

**Files:**
- Create: `cms_site/tests/test_public_content.py`
- Create: `cms_site/tests/test_query_performance.py`
- Modify: `cms_site/content/forms.py` (merge existing 366-day change)
- Modify: `cms_site/content/selectors.py` (preserve existing stable ordering)
- Modify: `cms_site/content/views.py`

**Interfaces:**
- Produces `BrowseCategoryForm` for `/list/?category=` validation.
- Produces `homepage_items(limit: int = 24) -> QuerySet[Item]` and grouped homepage context.
- Preserves `search_published_items(...)` signature and inclusive Shanghai date semantics.

- [ ] **Step 1: Write failing public-flow and query-count tests**

Cover title/date/category individual queries, AND combinations, inclusive end date, 366-day cap, invalid category/list/category values without 500, drafts hidden everywhere, stable pagination for equal timestamps, and query-count ceilings for homepage/list/search.

- [ ] **Step 2: Confirm invalid browse category and missing sections fail**

Run `manage.py test tests.test_public_content tests.test_query_performance -v 2`.

- [ ] **Step 3: Merge and complete forms/selectors/views**

Keep the existing user edits. Add a `BrowseCategoryForm` with `ModelChoiceField`; invalid values render an empty result and Chinese error instead of raising. Keep all public selectors ordered by `-publish_time, -pk`, select both category and author where templates use them, and group homepage content in Python from a bounded query rather than one query per category.

- [ ] **Step 4: Verify PostgreSQL plans on expanded data**

Create 10,000 records inside the performance test, run `ANALYZE content_item`, use QuerySet `.explain()` for title and category/time queries, and assert the GIN/composite index names appear. Mark this class `@tag('postgres_performance')` so it can run separately while remaining documented.

- [ ] **Step 5: Validate and commit**

Run LSP/Ruff, core public tests, then tagged performance tests. Commit message: `perf: 优化 PostgreSQL 内容查询与首页聚合`.

### Task 10: Download and provenance-track licensed BJTU assets

**Files:**
- Create: `cms_site/static/img/bjtu/logo.png`
- Create: `cms_site/static/img/bjtu/hero-01.jpg`
- Create: `cms_site/static/img/bjtu/hero-02.jpg`
- Create: `cms_site/static/img/bjtu/hero-03.jpg`
- Create: `cms_site/static/img/bjtu/hero-04.jpg`
- Create: `cms_site/static/img/bjtu/hero-05.jpg`
- Create: `docs/12_北交大官网素材来源与许可.md`
- Create: `cms_site/tests/test_static_assets.py`

**Interfaces:**
- Templates in Task 11 rely on exact `static/img/bjtu/*` paths.

- [ ] **Step 1: Write failing asset existence/signature tests**

Assert every file exists, logo starts with PNG signature, heroes start with JPEG signature, no file is empty, and the provenance document contains every source URL.

- [ ] **Step 2: Download exact approved sources locally**

Use `curl.exe --fail --location` after verifying the parent directory exists:

```text
https://www.bjtu.edu.cn/images/img2019/logo_01.png
https://www.bjtu.edu.cn/images/2026-04/af3631c78c334f56815b33f3ac98fb31.jpg
https://www.bjtu.edu.cn/images/2025-11/1327f795cea4469db03602c44d8b7bea.jpg
https://www.bjtu.edu.cn/images/2026-07/604735a54f1746748c24b4ef06a1965c.jpg
https://www.bjtu.edu.cn/images/2026-08/9a48dba706854b5889db46577e353173.jpg
https://www.bjtu.edu.cn/images/2024-09/a7e2d85be52f44b68d10a21c2a1a08d4.jpg
```

- [ ] **Step 3: Record evidence**

Document original URL, local filename, source dimensions, SHA-256 from `Get-FileHash`, fetch date `2026-08-14`, usage, and the user's statement that permission was obtained. State that runtime hotlinking is prohibited and the project is not an official site.

- [ ] **Step 4: Test and commit**

Run `manage.py test tests.test_static_assets -v 2`. Commit message: `assets: 本地化北交大官网授权视觉素材`.

### Task 11: BJTU main-site frontend and restrained Admin branding

**Files:**
- Create: `cms_site/tests/test_bjtu_templates.py`
- Modify: `cms_site/templates/base.html`
- Modify: `cms_site/templates/partials/nav.html`
- Modify: `cms_site/templates/content/index.html`
- Modify: `cms_site/templates/content/item_list.html`
- Modify: `cms_site/templates/content/search_form.html`
- Modify: `cms_site/templates/content/item_detail.html`
- Modify: `cms_site/templates/registration/login.html`
- Modify: `cms_site/templates/admin/base_site.html`
- Modify: `cms_site/static/css/tokens.css`
- Modify: `cms_site/static/css/custom.css` (preserve current error-page additions)
- Modify: `cms_site/static/css/admin.css`
- Modify: `cms_site/static/js/main.js`

**Interfaces:**
- Consumes Task 9 homepage context and Task 10 asset paths.
- Produces keyboard-accessible carousel with `[data-carousel]`, `[data-slide]`, previous/next and pause controls.

- [ ] **Step 1: Write failing template contract tests**

Assert local logo/hero paths, no Bootstrap CDN or external images, exact navigation labels 首页/栏目/文章/查询, login/logout/Admin conditions, “课程 CMS 原型，非官方网站”, school address/postcode, semantic headings, image alt text, and carousel controls.

- [ ] **Step 2: Confirm the current generic CMS layout fails**

Run `manage.py test tests.test_bjtu_templates -v 2`.

- [ ] **Step 3: Apply the verified BJTU visual tokens**

Set `--bjtu-blue: #005bac`, `--bjtu-footer: #065eb1`, `--bjtu-text: #333`, 1200px content width, Microsoft YaHei-first font stack, 90px desktop brand area, 46px navigation, 14px body, 16px/700 nav and 20px/700 section headings. Do not use gradients, decorative orbs, nested cards, negative letter spacing, or viewport-scaled font sizes.

- [ ] **Step 4: Rebuild page structures**

Homepage order: brand/navigation, full-width 2480:801 carousel, 交大头条, 教学科研/校园动态 two-column band, 通知公告, 校园影像, category links, footer. List/search use dense two-column article rows and bounded filter area. Detail uses a readable 45rem column. Login uses the same shell. Footer shows school address/postcode plus the non-official course statement; do not display the official ICP number as this prototype's registration.

- [ ] **Step 5: Brand Admin without replacing its operational layout**

Use the local logo and blue theme while retaining Django list filters, forms, tables, deletion confirmation and responsive horizontal table scrolling.

- [ ] **Step 6: Implement accessible responsive behavior**

At 992px collapse navigation; at 767px stack two-column sections; at 480px reduce padding while keeping 44px targets. JavaScript controls nav and carousel, updates `aria-expanded`/`aria-live`, supports keyboard arrows and pause, and disables autoplay for `prefers-reduced-motion`.

- [ ] **Step 7: Automated and browser verification**

Run template tests. Start the Compose site and use Playwright at 1440x1000, 768x1024, and 375x812. Verify no overlap/horizontal scroll, images are nonblank, carousel moves/pauses, all login roles, searches and Admin links work. Capture screenshots for the test report.

- [ ] **Step 8: Commit**

Commit message: `feat: 复刻北交大主站前台与后台品牌风格`.

### Task 12: Synchronize requirements, architecture, deployment, AI, and acceptance docs

**Files:**
- Modify: `README.md`
- Modify: `docs/01_需求分析文档.md`
- Modify: `docs/02_详细设计文档.md`
- Modify: `docs/04_概要设计文档.md`
- Modify: `docs/06_系统部署说明书.md`
- Create: `docs/03_PostgreSQL测试说明.md`
- Create: `docs/05_PostgreSQL测试报告.md`
- Create: `docs/07_AI使用说明_2026.md`
- Create: `docs/08_PostgreSQL技术报告.md`
- Create: `docs/09_CMS管理员操作说明.md`
- Create: `docs/10_人工验收流程.md`
- Create: `docs/11_核心模块答辩说明.md`
- Create: `docs/13_作业要求符合性矩阵.md`

**Interfaces:**
- Documents must use the exact env vars, usernames, commands, routes, table/index names and versions implemented above.

- [ ] **Step 1: Add a failing documentation consistency test**

Create `cms_site/tests/test_documentation.py` that asserts required files exist, README has PostgreSQL 18.6 and no MySQL/SQLite runtime instructions, no committed password appears, all referenced docs exist, and the compliance matrix contains every required assignment item.

- [ ] **Step 2: Update the three design levels and deployment guide**

Replace all SQLite/MySQL architecture, ER, sequence, deployment and decision text with PostgreSQL 18.6, three core tables, pg_trgm/GIN/composite indexes, superuser role rule, logs, Docker Compose and the approved UI architecture. Correct earlier placeholders for author/reviewer with “学生填写” rather than fabricated identity.

- [ ] **Step 3: Write operational and test documents**

Include exact clean-install commands, `.env` variables, `docker compose up --build --wait`, two seed runs, demo usernames, password-source rules, three query demos, Admin CRUD, log filters, health endpoints, backup/reset warning, and native PostgreSQL steps.

- [ ] **Step 4: Write transparent AI and source disclosure**

Record GPT-5.6 Sol/Sisyphus, sequential-thinking, Context7, CodeGraph, BasedPyright LSP, Playwright and web research; include representative user prompts, accepted choices, rejected alternatives (strict three physical tables, custom user, custom CRUD backend, SQLite tests), human verification responsibilities, no sensitive-data upload, and link to the asset provenance document.

- [ ] **Step 5: Write explainability and compliance material**

Explain model relationships, QuerySet laziness, form-cleaning boundaries, date conversion, index tradeoffs, transaction-on-commit cache invalidation, role flag synchronization, log redaction, Docker dependency order and known admin-superuser risk. Map each assignment requirement to implementation file, test, manual evidence and status.

- [ ] **Step 6: Test and split documentation commits**

Run `manage.py test tests.test_documentation -v 2`. Commit architecture/deployment docs as `docs: 同步 PostgreSQL 架构与部署说明`; commit test/AI/acceptance docs separately as `docs: 补齐测试 AI 与课程验收材料`.

### Task 13: Full clean-environment verification and evidence closure

**Files:**
- Modify: `docs/05_PostgreSQL测试报告.md` with actual results only
- Modify: `docs/10_人工验收流程.md` with actual screenshot/evidence paths

**Interfaces:**
- Uses a unique Compose project `cms-postgres-validation` so verification never deletes pre-existing volumes.

- [ ] **Step 1: Run static and migration gates**

```powershell
cd cms_site
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe manage.py makemigrations --check
.\.venv\Scripts\python.exe manage.py check
```

Run BasedPyright LSP diagnostics on every changed Python file. Expected: no errors or warnings attributable to this work.

- [ ] **Step 2: Run PostgreSQL-only test and coverage gates**

```powershell
docker compose -p cms-postgres-validation up -d db redis
docker compose -p cms-postgres-validation run --rm test
```

Expected: the test service runs coverage and the threshold check in one container; all tests pass and core modules reach at least 80% coverage.

- [ ] **Step 3: Prove clean migration and idempotent data**

Start the validation stack from its empty volume, run `showmigrations`, `verify_postgres`, and `seed_data` twice. Query counts for the three core tables, verify exactly 8 categories, 36 articles, 3 drafts, 4 users, `pg_trgm`, and three named indexes.

- [ ] **Step 4: Run security and production checks**

Run `manage.py check --deploy` with public-mode variables, confirm no secret values appear in logs, ordinary users cannot access Admin/logs, query strings and credentials are absent from JSONL, and readiness returns 503 when PostgreSQL or Redis is unavailable.

- [ ] **Step 5: Run manual browser acceptance**

Use Playwright to execute anonymous browsing, all three search modes and a combination, normal-user login/logout, admin-user login, user role change, category CRUD, article draft/publish/delete, protected category deletion, audit lookup and request-log filtering at desktop/mobile viewports.

- [ ] **Step 6: Record actual evidence and clean only validation resources**

Write command versions, pass counts, coverage, PostgreSQL version, index-plan excerpts, screenshots and observed results into the reports. Then run `docker compose -p cms-postgres-validation down --volumes`; this only removes the validation project's new volumes. Remove only test artifacts generated by this run.

- [ ] **Step 7: Final repository review and commit**

Confirm `git status` still shows any unrelated pre-existing user changes and that they were not staged. Review every task commit, then commit only evidence docs as `test: 记录 PostgreSQL CMS 完整验收证据`.

## Completion Checklist

- [ ] No runtime/test references to MySQL, PyMySQL, `DB_ENGINE`, or SQLite remain outside historical design records explicitly labeled obsolete.
- [ ] PostgreSQL reports 18.6 and all migrations/indexes/extensions exist.
- [ ] Three core tables, four demo users, eight categories, 36 articles and three drafts match the spec.
- [ ] Normal/admin authentication and authorization are proven both by tests and browser use.
- [ ] User/content/audit/request-log Admin workflows are complete and read-only boundaries hold.
- [ ] All assets are local, licensed/provenanced and visually rendered.
- [ ] Ruff, LSP, Django checks, migrations, tests, coverage, query plans, Compose health and Playwright pass.
- [ ] Documentation and AI disclosure match actual code and evidence.
- [ ] Every commit is focused and no unrelated dirty-worktree changes were included.
