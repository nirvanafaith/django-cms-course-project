@echo off
chcp 65001 >nul
setlocal EnableExtensions

title CMS Public cpolar Mode
set "PROJECT_ROOT=%~dp0"
set "CMS_DIR=%PROJECT_ROOT%cms_site"
set "PYTHON_EXE=%CMS_DIR%\.venv\Scripts\python.exe"
set "CPOLAR_DEFAULT=C:\Program Files\cpolar\cpolar.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python virtual environment not found: %PYTHON_EXE%
    exit /b 1
)

if not defined CPOLAR_EXE set "CPOLAR_EXE=%CPOLAR_DEFAULT%"
if not exist "%CPOLAR_EXE%" (
    echo [ERROR] cpolar not found. Install it or set CPOLAR_EXE.
    exit /b 1
)

for %%V in (
    DJANGO_SECRET_KEY
    POSTGRES_DB
    POSTGRES_USER
    POSTGRES_PASSWORD
    POSTGRES_HOST
    POSTGRES_PORT
    REDIS_URL
    DEMO_USER_PASSWORD
    DEMO_ADMIN_PASSWORD
) do (
    if not defined %%V (
        echo [ERROR] %%V is required for public mode.
        exit /b 1
    )
)

cd /d "%CMS_DIR%"
if errorlevel 1 exit /b 1

echo [INFO] Running public deployment checks, then starting cpolar HTTPS tunnel and Waitress...
"%PYTHON_EXE%" manage.py serve_public
if errorlevel 1 (
    echo [ERROR] Public CMS startup failed.
    exit /b 1
)

exit /b 0
