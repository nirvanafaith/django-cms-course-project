@echo off
chcp 65001 >nul
setlocal

title CMS PostgreSQL Local Mode
set "PROJECT_ROOT=%~dp0"

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or is not available in PATH.
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running.
    exit /b 1
)

cd /d "%PROJECT_ROOT%"
if errorlevel 1 (
    echo [ERROR] Cannot enter project directory: %PROJECT_ROOT%
    exit /b 1
)

echo Building and starting PostgreSQL, Redis, migrations and CMS...
docker compose up --build --wait
if errorlevel 1 exit /b 1

echo Frontend: http://127.0.0.1:8000/
echo Admin:    http://127.0.0.1:8000/admin/
start "" http://127.0.0.1:8000/

exit /b 0
