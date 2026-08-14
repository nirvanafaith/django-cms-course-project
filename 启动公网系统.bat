@echo off
chcp 65001 >nul
setlocal

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

if not defined DJANGO_SECRET_KEY (
    echo [ERROR] DJANGO_SECRET_KEY is required for public mode.
    exit /b 1
)
if not defined POSTGRES_DB (
    echo [ERROR] POSTGRES_DB, POSTGRES_USER and POSTGRES_PASSWORD are required.
    exit /b 1
)
if not defined REDIS_URL (
    echo [ERROR] REDIS_URL is required for public mode.
    exit /b 1
)

cd /d "%CMS_DIR%"
if errorlevel 1 exit /b 1

echo Starting cpolar HTTPS tunnel and Waitress...
"%PYTHON_EXE%" manage.py serve_public
if errorlevel 1 exit /b 1

exit /b 0
