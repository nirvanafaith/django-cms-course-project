# PostgreSQL CMS 测试说明

## 1. 测试目标

验证 PostgreSQL-only 运行链路、数据约束、公开查询、角色授权、后台管理、结构化日志、素材和北交大风格模板。测试不得依赖宿主机已有数据库；Docker Compose 测试服务创建独立测试库。

## 2. 自动化分层

| 层级 | 主要模块 | 目的 |
| --- | --- | --- |
| 配置与运行时 | `test_database_config`、`test_runtime_config`、`test_verify_postgres` | 仅接受 PostgreSQL 18 及以上 |
| 数据模型 | `test_postgresql_models` | 默认草稿、外键、索引和 `pg_trgm` |
| 业务流程 | `test_public_content`、`test_authentication`、`test_admin_management` | 浏览、搜索、权限与 CRUD |
| 支撑服务 | `core.tests` | 缓存、日志、日志阅读、健康与部署前检查 |
| 前端和交付 | `test_bjtu_templates`、`test_static_assets`、`test_documentation` | 本地素材、模板合同和文档一致性 |

## 3. 运行命令

在仓库根目录设置必需环境变量后执行：

```powershell
docker compose -p cms-postgresql-validation up -d db redis
docker compose -p cms-postgresql-validation run --rm --build test
docker compose -p cms-postgresql-validation run --rm test python manage.py test tests.test_query_performance -v 2
```

测试服务执行 coverage，并要求核心模块覆盖率不低于 80%。性能测试带 `postgres_performance` 标签，使用扩展数据和 `QuerySet.explain()`，验证标题 GIN 和栏目/时间组合索引进入计划。

## 4. 静态门禁

在 `cms_site/` 中执行：

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
& 'C:\Users\ctx75\.local\bin\basedpyright.exe' <改动的 Python 文件>
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check
```

LSP MCP 的请求根目录受会话环境限制时，使用同一 BasedPyright 引擎的 CLI 诊断并保留命令输出。最终报告只记录实际运行结果。

## 5. 环境与清理

干净验收从空 Compose 卷开始。结束后仅清理本验证项目：

```powershell
docker compose -p cms-postgresql-validation down --volumes
docker compose -p cms-postgresql-uiqa down --volumes
```

不得清理其他 Compose 项目、用户数据卷或未归属本轮的工作文件。
