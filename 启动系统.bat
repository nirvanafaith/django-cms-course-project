@echo off
chcp 65001 >nul
setlocal

title CMS Local Mode
set "PROJECT_ROOT=%~dp0"
set "CMS_DIR=%PROJECT_ROOT%cms_site"
set "PYTHON_EXE=%CMS_DIR%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python virtual environment not found: %PYTHON_EXE%
    exit /b 1
)

cd /d "%CMS_DIR%"
if errorlevel 1 (
    echo [ERROR] Cannot enter project directory: %CMS_DIR%
    exit /b 1
)

set "DJANGO_MODE=local"
echo [1/5] Checking MySQL and cache configuration...
"%PYTHON_EXE%" manage.py preflight --mode local
if errorlevel 1 exit /b 1

echo [2/5] Applying database migrations...
"%PYTHON_EXE%" manage.py migrate --noinput
if errorlevel 1 exit /b 1

echo [3/5] Initializing demo data...
"%PYTHON_EXE%" manage.py seed_data
if errorlevel 1 exit /b 1

echo [4/5] Collecting static files...
"%PYTHON_EXE%" manage.py collectstatic --noinput
if errorlevel 1 exit /b 1

echo [5/5] Starting Waitress at http://127.0.0.1:8000/
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000/"
"%PYTHON_EXE%" manage.py serve_waitress
if errorlevel 1 exit /b 1

exit /b 0
