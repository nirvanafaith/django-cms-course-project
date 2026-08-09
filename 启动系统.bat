@echo off
chcp 936 >nul
setlocal

title CMS 系统一键启动

set "PROJECT_ROOT=%~dp0"
set "CMS_DIR=%PROJECT_ROOT%cms_site"
set "PYTHON_EXE=%CMS_DIR%\.venv\Scripts\python.exe"
set "PIP_EXE=%CMS_DIR%\.venv\Scripts\pip.exe"
set "SITE_URL=http://127.0.0.1:8000/"
set "ADMIN_URL=http://127.0.0.1:8000/admin/"

cd /d "%CMS_DIR%"
if errorlevel 1 (
    echo [错误] 无法进入项目目录: %CMS_DIR%
    pause
    exit /b 1
)

echo ==========================================
echo   CMS 内容管理系统 - 一键启动
echo   按 Ctrl+C 可停止服务器
echo ==========================================
echo.

if not exist "%PYTHON_EXE%" (
    echo [错误] 未找到虚拟环境: %PYTHON_EXE%
    echo 请先按部署手册配置环境: %PROJECT_ROOT%docs\06_系统部署说明书.md
    pause
    exit /b 1
)

"%PYTHON_EXE%" -c "import django" >nul 2>&1
if errorlevel 1 (
    echo [错误] 虚拟环境中未安装 Django。
    echo 请执行: %PIP_EXE% install -r %CMS_DIR%\requirements.txt
    pause
    exit /b 1
)

if not exist "logs" mkdir "logs"

echo [1/3] 正在执行数据库迁移...
"%PYTHON_EXE%" manage.py migrate
if errorlevel 1 (
    echo [错误] 数据库迁移失败。
    pause
    exit /b 1
)

echo [2/3] 正在初始化演示数据...
"%PYTHON_EXE%" manage.py seed_data

echo [3/3] 正在启动服务器: %SITE_URL%
echo 前台首页: %SITE_URL%
echo 后台管理: %ADMIN_URL%
echo.

start "" /b cmd /c "timeout /t 3 /nobreak >nul & start %SITE_URL%"

"%PYTHON_EXE%" manage.py runserver 127.0.0.1:8000

echo.
echo 服务器已停止。
pause