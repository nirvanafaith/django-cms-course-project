@echo off
chcp 65001 >nul
setlocal EnableExtensions

title CMS PostgreSQL Local Mode
set "PROJECT_ROOT=%~dp0"
set "APP_URL=http://127.0.0.1:8000/"

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

if not exist "%PROJECT_ROOT%compose.yaml" (
    echo [ERROR] compose.yaml was not found in %PROJECT_ROOT%
    exit /b 1
)

docker compose config --quiet
if errorlevel 1 (
    echo [ERROR] Compose configuration is invalid. Check required environment variables.
    exit /b 1
)

echo [INFO] Rebuilding PostgreSQL, Redis, migrations and the CMS web service...
docker compose up -d --build --wait --remove-orphans web
if errorlevel 1 (
    echo [ERROR] CMS startup failed. Run "docker compose logs --tail 100" for details.
    exit /b 1
)

docker compose ps
echo Frontend: %APP_URL%
echo Admin:    %APP_URL%admin/
if not defined CMS_NO_BROWSER start "" "%APP_URL%"

exit /b 0
