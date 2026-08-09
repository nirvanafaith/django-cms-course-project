# Django CMS 课程项目

一个面向课程设计与教学演示的内容管理系统。项目基于 Django 5.2，提供栏目与文章管理、公开内容浏览、组合搜索、分页、发布状态控制和可复现演示数据，并配有完整的需求、设计、测试、部署与答辩文档。

## 技术栈

- Python 3.12、Django 5.2
- SQLite（本地开发与课程演示）
- Django Templates、原生 CSS 与 JavaScript
- Django TestCase、Ruff

## 项目结构

```
├── cms_site/            # Django 项目根（manage.py 所在）
│   ├── config/          # 项目配置包（settings/urls/wsgi/asgi）
│   ├── content/         # 业务应用（模型/查询器/表单/视图/Admin）
│   │   ├── models.py     # Category/Item 与 ItemQuerySet.published()
│   │   ├── selectors.py  # 前台只读 ORM 查询
│   │   ├── pagination.py # 分页和翻页参数工具
│   │   ├── forms.py      # SearchForm 输入校验与类型转换
│   │   └── views.py      # HTTP 请求/响应编排
│   ├── templates/       # 页面模板
│   ├── static/          # 静态资源
│   └── requirements.txt # 依赖锁定
├── docs/                # 交付文档（V 模型文档链 + 技术报告）
└── .gitignore
```

## 功能

- 通过 Django Admin 管理栏目和文章，支持批量发布与撤回
- 公开首页、栏目列表和文章详情只展示已发布内容
- 按标题、发表时间和栏目进行独立或组合查询
- 搜索条件随分页链接保留，非法日期和页码可安全处理
- 使用 `select_related`、聚合查询和数据库索引控制常见查询开销
- 使用 `python manage.py seed_data` 生成固定的 5 个栏目和 63 篇演示文章
- 自动化测试覆盖模型、表单、查询器、分页、视图、Admin、安全与 UI 上下文

## 快速开始

### 首次安装

```powershell
git clone https://github.com/nirvanafaith/django-cms-course-project.git
cd django-cms-course-project
cd cms_site
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

之后可双击项目根目录的 `启动系统.bat`。脚本会执行迁移、幂等初始化演示数据、启动开发服务器并打开浏览器；使用前需完成上述虚拟环境和依赖安装。

- 前台首页：http://127.0.0.1:8000/
- 后台管理：http://127.0.0.1:8000/admin/

完整部署步骤见 `docs/06_系统部署说明书.md`；技术论证见 `docs/08_技术报告.md`。

## 测试与质量检查

在 `cms_site` 目录执行：

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe -m ruff check .
```

项目数据库、虚拟环境、日志、上传文件和工具缓存均由 `.gitignore` 排除。生产部署时请通过环境变量设置 `DJANGO_SECRET_KEY`、`DJANGO_DEBUG` 和 `DJANGO_ALLOWED_HOSTS`，不要使用开发默认值。

## 文档索引

| 文档 | 说明 |
| --- | --- |
| `docs/00_交付物与符合性对照.md` | 交付物清单与题目符合性总览 |
| `docs/01_需求分析文档.md` | 需求基线（FR/NFR） |
| `docs/02_详细设计文档.md` | 数据库/表单/视图/Admin/安全/取舍 |
| `docs/03_测试文档.md` | 测试用例设计与测试分类 |
| `docs/04_概要设计文档.md` | 模块划分与接口设计 |
| `docs/05_测试报告.md` | 测试执行结果（编码后回填） |
| `docs/06_系统部署说明书.md` | 部署/迁移/启动/测试 |
| `docs/07_AI使用说明.md` | AI 使用透明化声明 |
| `docs/08_技术报告.md` | 技术路线/BCNF 证明/算法复杂度/实现计划 |
| `docs/09_操作说明书.md` | 前台/后台操作手册（用户与管理员） |
| `docs/10_人工验收测试流程表.md` | 人工操作验收执行表（48 项） |
| `docs/11_答辩报告.md` | 面向初学者的逐文件、逐函数、逐变量答辩说明 |
