@echo off
chcp 65001 >nul
setlocal EnableExtensions

title CMS PostgreSQL Local Mode
set "PROJECT_ROOT=%~dp0"
set "APP_URL=http://127.0.0.1:8000/"
set "EXIT_CODE=0"

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or is not available in PATH.
    set "EXIT_CODE=1"
    goto :finish
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running.
    set "EXIT_CODE=1"
    goto :finish
)

cd /d "%PROJECT_ROOT%"
if errorlevel 1 (
    echo [ERROR] Cannot enter project directory: %PROJECT_ROOT%
    set "EXIT_CODE=1"
    goto :finish
)

if not exist "%PROJECT_ROOT%compose.yaml" (
    echo [ERROR] compose.yaml was not found in %PROJECT_ROOT%
    set "EXIT_CODE=1"
    goto :finish
)

docker compose config --quiet
if errorlevel 1 (
    echo [ERROR] Compose configuration is invalid. Check required environment variables.
    set "EXIT_CODE=1"
    goto :finish
)

echo [INFO] Rebuilding PostgreSQL, Redis, migrations and the CMS web service...
echo Frontend: %APP_URL%
echo Admin:    %APP_URL%admin/
echo [INFO] Container logs will stream below. Press Ctrl+C to stop the local CMS containers.
if not defined CMS_NO_BROWSER start "" "%APP_URL%"
docker compose up --build --remove-orphans --abort-on-container-failure web
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] CMS stopped with exit code %EXIT_CODE%.
    goto :finish
)

:finish
echo.
echo Frontend: %APP_URL%
echo Admin:    %APP_URL%admin/
docker compose ps
echo [INFO] Launcher exit code: %EXIT_CODE%.
echo [INFO] Press any key to close this window.
pause >nul
exit /b %EXIT_CODE%
