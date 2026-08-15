# PostgreSQL CMS 测试报告

| 项目 | 内容 |
| --- | --- |
| 报告状态 | Task 13 执行中，以下记录仅为已完成阶段的实际结果 |
| 测试环境 | Docker Desktop、PostgreSQL 18.6、Redis 7.4、Python 3.12、Django 5.2 |
| 记录人/复核人 | 学生填写 |

## 1. 已完成自动化结果

| 日期 | 命令/范围 | 实际结果 |
| --- | --- | --- |
| 2026-08-15 | Task 9 全量 Compose 测试 | 71/71 通过，coverage 80% |
| 2026-08-15 | `tests.test_query_performance` | 2/2 通过，两个命名查询索引进入 EXPLAIN 计划 |
| 2026-08-15 | Task 11 模板与素材合同 | 9/9 通过 |
| 2026-08-15 | Task 11 类型检查 | BasedPyright 0 errors、0 warnings |

## 2. 已观察数据库对象

- `verify_postgres` 要求 PostgreSQL 服务端主版本不低于 18。
- 迁移启用 `pg_trgm`。
- `content_item` 使用 `item_pub_time_idx`、`item_cat_pub_time_idx`、`item_title_trgm_idx`。

## 3. 前端证据

Task 11 的初始验收截图已归档在 `docs/evidence/`：桌面、平板、移动首页，普通用户移动首页，移动搜索页和移动后台。最终 Task 13 会补充 CRUD、日志筛选、健康降级和最终全量测试输出，并更新此报告。

## 4. 最终记录模板

| 项目 | 最终实际值 |
| --- | --- |
| 全量测试通过数 / 覆盖率 | 待 Task 13 回填 |
| 性能测试通过数 / EXPLAIN 摘录 | 待 Task 13 回填 |
| 干净环境对象计数 | 待 Task 13 回填 |
| 静态门禁 | 待 Task 13 回填 |
| 浏览器验收 | 待 Task 13 回填 |

本报告不使用估算结果替代最终命令输出。
