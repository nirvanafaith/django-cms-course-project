# Django CMS 课程项目

一个面向课程设计与教学演示的内容管理系统。项目基于 Django 5.2，提供栏目与文章管理、公开内容浏览、组合搜索、分页、发布状态控制和可复现演示数据，并配有完整的需求、设计、测试、部署与答辩文档。

## 技术栈

- Python 3.12、Django 5.2
- SQLite（本地开发与课程演示）
- Django Templates、原生 CSS 与 JavaScript
- Waitress、WhiteNoise、MySQL、Redis、cpolar

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
│   ├── core/             # 健康检查、缓存、限流与部署命令
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
- Waitress 8 线程并发服务，Redis 热点缓存与 Admin 登录限流
- cpolar 随机 HTTPS 域名公网访问，严格 Host/CSRF 校验
- Docker Compose 一键集成 Waitress、MySQL 与 Redis

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
set DB_ENGINE=mysql
set DB_NAME=cms
set DB_USER=cms_user
set DB_PASSWORD=你的数据库密码
set REDIS_URL=redis://127.0.0.1:6379/0
```

之后可双击项目根目录的 `启动系统.bat`。脚本会检查 MySQL/Redis、执行迁移、初始化演示数据、收集静态文件并以 Waitress 启动本地服务。

公网模式还需设置 `DJANGO_SECRET_KEY`，完成一次 `cpolar authtoken <你的令牌>`，然后双击 `启动公网系统.bat`。脚本会建立随机 HTTPS 隧道并输出、打开公网地址。凭据不得写入 BAT。

- 前台首页：http://127.0.0.1:8000/
- 后台管理：http://127.0.0.1:8000/admin/

完整部署步骤见 `docs/06_系统部署说明书.md`；技术论证见 `docs/08_技术报告.md`。

项目数据库、虚拟环境、日志、上传文件和工具缓存均由 `.gitignore` 排除。正式运行必须使用 MySQL；SQLite 只允许通过 `DB_ENGINE=sqlite` 显式用于本地开发。公网启动器会自动注入随机域名对应的 Host 与 CSRF 配置。

### Docker Compose

安装 Docker Desktop 或 Docker Engine 后，在项目根目录执行：

```powershell
Copy-Item .env.example .env
# 将 .env 中的三个 replace-with-* 值替换为独立的随机密钥
docker compose up --build --wait
docker compose logs -f web
```

Compose 只向宿主机 `127.0.0.1` 发布 Web 端口，MySQL 和 Redis 仅在容器网络内可见。`migrate` 服务会在依赖健康后执行迁移和幂等演示数据初始化，成功退出后才启动 Web。

停止服务使用 `docker compose down`。MySQL 数据保存在 `mysql-data` 命名卷中；`docker compose down -v` 会永久删除该卷，只能在确认需要重置数据时执行。

## 文档索引

| 文档 | 说明 |
| --- | --- |
| `docs/01_需求分析文档.md` | 需求基线（FR/NFR） |
| `docs/02_详细设计文档.md` | 数据库/表单/视图/Admin/安全/取舍 |
| `docs/04_概要设计文档.md` | 模块划分与接口设计 |
| `docs/06_系统部署说明书.md` | 部署/迁移/启动/测试 |
