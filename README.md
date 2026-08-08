# 基于 Python/Django 的 CMS 原型系统

北京交通大学 CITEL_T_001 课程作业：基于 Python + Django 的内容管理原型系统。

## 项目结构

```
├── cms_site/            # Django 项目根（manage.py 所在）
│   ├── config/          # 项目配置包（settings/urls/wsgi/asgi）
│   ├── content/         # 业务应用（栏目 Category / 文章 Item）
│   ├── templates/       # 页面模板
│   ├── static/          # 静态资源
│   └── requirements.txt # 依赖锁定
├── docs/                # 交付文档（V 模型文档链 + 技术报告）
└── .gitignore
```

## 功能

- 栏目/文章增删改查（Django Admin，管理用户）
- 普通用户浏览已发布文章（首页/栏目列表/详情）
- 前台三种查询模式：按题目、按发表时间、按栏目（可组合、分页）
- 发布状态控制（草稿前台不可见）
- 演示数据一键生成（`manage.py seed_data`）

## 快速开始

**一键启动（推荐）**：双击项目根目录 `启动系统.bat`——自动迁移/初始化数据/启动服务，并自动打开浏览器。

命令行方式：

```powershell
cd cms_site
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser   # 演示账号 admin / admin123456
python manage.py runserver
```

- 前台首页：http://127.0.0.1:8000/
- 后台管理：http://127.0.0.1:8000/admin/

完整部署步骤见 `docs/06_系统部署说明书.md`；技术论证见 `docs/08_技术报告.md`。

## 文档索引

| 文档 | 说明 |
| --- | --- |
| `docs/00_交付物与符合性对照.md` | 交付物清单与题目符合性总览 |
| `docs/01_需求分析文档.md` | 需求基线（FR/NFR） |
| `docs/02_详细设计文档.md` | 数据库/表单/视图/Admin/安全/取舍 |
| `docs/03_测试文档.md` | 测试用例设计（54 例） |
| `docs/04_概要设计文档.md` | 模块划分与接口设计 |
| `docs/05_测试报告.md` | 测试执行结果（编码后回填） |
| `docs/06_系统部署说明书.md` | 部署/迁移/启动/测试 |
| `docs/07_AI使用说明.md` | AI 使用透明化声明 |
| `docs/08_技术报告.md` | 技术路线/BCNF 证明/算法复杂度/实现计划 |
| `docs/09_操作说明书.md` | 前台/后台操作手册（用户与管理员） |
| `docs/10_人工验收测试流程表.md` | 人工操作验收执行表（48 项） |
