# PostgreSQL CMS 测试报告

| 项目 | 内容 |
| --- | --- |
| 报告状态 | Task 13 已完成（2026-08-15） |
| 测试环境 | Docker Desktop、PostgreSQL 18.6、Redis 7.4、Python 3.12、Django 5.2 |
| 记录人/复核人 | 学生填写 |

## 1. 已完成自动化结果

| 日期 | 命令/范围 | 实际结果 |
| --- | --- | --- |
| 2026-08-15 | 最终全量 Compose 测试 | 85/85 通过，分支覆盖率 80%（门槛 80%） |
| 2026-08-15 | `tests.test_query_performance` | 2/2 通过；标题 Trigram GIN 与栏目/时间复合索引均进入 EXPLAIN 计划 |
| 2026-08-15 | 静态与类型门禁 | Ruff check/format 通过；BasedPyright 0 errors、0 warnings；Django check 与 Compose 内 makemigrations --check 通过 |
| 2026-08-15 | 生产配置检查 | `manage.py check --deploy` 通过（2 项项目配置明确静默） |

## 2. 已观察数据库对象

- 空 Compose 卷从零执行迁移，`content` 的 `0001_initial`、`0002_postgresql_constraints_indexes`、`0003_upper_title_trigram_index` 均已应用。
- `verify_postgres` 实际输出 `PostgreSQL 18.6 验证通过`。
- 迁移后的对象计数为 8 个栏目、36 篇文章、3 篇草稿、4 个用户。
- 首次 `seed_data` 输出“创建 48，更新 0，跳过 0，草稿 3”；连续两次输出“创建 0，更新 0，跳过 48，草稿 3”。
- 真实数据库中存在 `pg_trgm` 与 `item_pub_time_idx`、`item_cat_pub_time_idx`、`item_title_trgm_idx`。

## 3. 前端证据

当前构建的首页截图：`docs/evidence/task13-home-desktop.png`（1440×1000）、`task13-home-tablet.png`（768×1024）、`task13-home-mobile.png`（375×812）；管理员移动页为 `task13-admin-mobile.png`。早期 Task 11 截图一并保留用于展示首页、搜索、普通用户和后台移动状态。

浏览器验收覆盖匿名、本地资源、题目搜索（“交通”5 篇）、日期加栏目组合（1 篇）、普通用户登录/退出与 Admin 拒绝、管理员入口、文章草稿到发布、文章删除、空栏目删除、含文章栏目保护删除、角色升降级与恢复、审计只读和系统日志筛选。数据库与 Redis 分别停机时，真实 `/health/ready/` 都返回 503；修复后不会因请求日志惰性用户解析把该状态改为 500。

## 4. 清理记录

本轮临时文章、临时栏目和临时角色提升已在 UIQA 项目中删除或还原。验证项目和 UIQA 项目将在提交前以各自 Compose 项目名执行 `down --volumes`；不会影响其他 Docker 项目。
