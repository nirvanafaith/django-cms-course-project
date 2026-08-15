# PostgreSQL BJTU CMS 课程项目

面向课程设计和教学演示的 Django 内容管理系统。系统以 PostgreSQL 18.6 为唯一业务数据库，提供公开内容浏览、题目/日期/栏目组合查询、普通用户登录、超级用户管理、结构化日志和可复现演示数据。

## 技术栈

- Python 3.12、Django 5.2、PostgreSQL 18.6、Psycopg 3
- Redis 7.4、Waitress、WhiteNoise、Docker Compose
- Django Templates、原生 CSS/JavaScript、Ruff、BasedPyright、coverage.py

## 功能与数据

- 公开路由：`/`、`/list/`、`/search/`、`/item/<pk>/`。
- 管理路由：`/admin/`、`/admin/system-logs/`；只有超级用户可以进入。
- 已发布内容支持题目、上海自然日发表时间、栏目三个条件的任意组合；草稿不会出现在公开页面。
- `seed_data` 幂等生成 8 个栏目、36 篇文章（其中 3 篇草稿）和 4 个用户。普通用户为 `student`、`visitor`，管理员为 `cms_admin`、`content_admin`。
- 演示密码只通过 `DEMO_USER_PASSWORD` 与 `DEMO_ADMIN_PASSWORD` 环境变量提供，绝不写入仓库或交付文档。

## Docker Compose 快速开始

安装 Docker Desktop 后，在仓库根目录设置当前终端的环境变量：

```powershell
$env:DJANGO_SECRET_KEY='使用密码管理器生成的随机长密钥'
$env:POSTGRES_PASSWORD='为数据库账户生成的独立随机密码'
$env:DEMO_USER_PASSWORD='为普通演示用户设置的临时密码'
$env:DEMO_ADMIN_PASSWORD='为管理员演示用户设置的独立临时密码'
docker compose up --build --wait
```

访问 `http://127.0.0.1:8000/`，后台入口为 `http://127.0.0.1:8000/admin/`。Compose 依次等待 PostgreSQL 与 Redis 健康，执行迁移、`verify_postgres`、`seed_data` 和 `collectstatic`，再启动 Web 服务。

查看状态与日志：

```powershell
docker compose ps
docker compose logs -f web
Invoke-WebRequest http://127.0.0.1:8000/health/live/
Invoke-WebRequest http://127.0.0.1:8000/health/ready/
```

`docker compose down` 停止服务并保留数据卷；`docker compose down --volumes` 会删除 PostgreSQL 数据，只有需要完全重置时才可使用。

## 本地开发与检查

在 `cms_site/` 中使用已安装的虚拟环境，并先配置 `POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_HOST`、`POSTGRES_PORT`。完整流程见 [部署说明](docs/06_系统部署说明书.md)。

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check
```

## 文档索引

| 文档 | 说明 |
| --- | --- |
| `docs/01_需求分析文档.md` | 需求与验收基线 |
| `docs/02_详细设计文档.md` | 数据、模块、安全与查询设计 |
| `docs/03_PostgreSQL测试说明.md` | 自动化与数据库测试方法 |
| `docs/04_概要设计文档.md` | 架构、接口和部署概览 |
| `docs/05_PostgreSQL测试报告.md` | 实际测试证据与结果 |
| `docs/06_系统部署说明书.md` | 部署、启动、备份与故障处理 |
| `docs/07_AI使用说明_2026.md` | AI 使用范围与人工核验 |
| `docs/08_PostgreSQL技术报告.md` | 技术取舍与性能论证 |
| `docs/09_CMS管理员操作说明.md` | 管理员操作流程 |
| `docs/10_人工验收流程.md` | 浏览器验收步骤与证据 |
| `docs/11_核心模块答辩说明.md` | 核心模块解释提纲 |
| `docs/12_北交大官网素材来源与许可.md` | 本地素材来源与许可记录 |
| `docs/13_作业要求符合性矩阵.md` | 需求到代码、测试和证据的追溯 |
