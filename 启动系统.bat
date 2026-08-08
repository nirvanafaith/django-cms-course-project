@echo off
title CMS 原型系统 - 一键启动
cd /d "%~dp0cms_site"

echo ==========================================
echo   CMS 原型系统 - 一键启动
echo   (按 Ctrl+C 可停止服务)
echo ==========================================
echo.

REM 1. 检查虚拟环境
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境 .venv，请先按 docs\06_系统部署说明书.md 第 2.2 步创建。
    pause
    exit /b 1
)

REM 2. 检查依赖
.venv\Scripts\python.exe -c "import django" >nul 2>&1
if errorlevel 1 (
    echo [错误] Django 未安装，请执行：.venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM 3. 数据库迁移（幂等，可重复执行）
echo [1/3] 检查数据库迁移...
.venv\Scripts\python.exe manage.py migrate >nul 2>&1
if errorlevel 1 (
    echo [错误] 数据库迁移失败，请检查 Python 环境。
    pause
    exit /b 1
)

REM 4. 演示数据（幂等，已存在则跳过）
echo [2/3] 初始化演示数据（已存在则跳过）...
.venv\Scripts\python.exe manage.py seed_data >nul 2>&1

REM 5. 启动服务并自动打开浏览器
echo [3/3] 启动服务：http://127.0.0.1:8000/
echo.
echo 浏览器将自动打开，若未打开请手动访问 http://127.0.0.1:8000/
echo 管理后台：http://127.0.0.1:8000/admin/
echo.

REM 3 秒后打开默认浏览器（等待服务就绪）
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8000"

REM 前台运行服务（窗口保持打开，日志可见）
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000

echo.
echo 服务已停止。
pause
