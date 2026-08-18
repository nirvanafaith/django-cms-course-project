@echo off
chcp 65001 >nul
setlocal EnableExtensions

title CMS Public cpolar Mode
set "PROJECT_ROOT=%~dp0"
set "CMS_DIR=%PROJECT_ROOT%cms_site"
set "PYTHON_EXE=%CMS_DIR%\.venv\Scripts\python.exe"
set "CPOLAR_DEFAULT=C:\Program Files\cpolar\cpolar.exe"
set "EXIT_CODE=0"

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python virtual environment not found: %PYTHON_EXE%
    set "EXIT_CODE=1"
    goto :finish
)

if not defined CPOLAR_EXE set "CPOLAR_EXE=%CPOLAR_DEFAULT%"
if not exist "%CPOLAR_EXE%" (
    echo [ERROR] cpolar not found. Install it or set CPOLAR_EXE.
    set "EXIT_CODE=1"
    goto :finish
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
) do (
    if not defined %%V (
        echo [ERROR] %%V is required for public mode.
        set "EXIT_CODE=1"
        goto :finish
    )
)

cd /d "%CMS_DIR%"
if errorlevel 1 (
    echo [ERROR] Cannot enter CMS directory: %CMS_DIR%
    set "EXIT_CODE=1"
    goto :finish
)

echo [INFO] Running public deployment checks, then starting cpolar HTTPS tunnel and Waitress...
echo [INFO] The public URL will be printed after the HTTPS tunnel is ready.
echo [INFO] Press Ctrl+C to stop the public CMS service.
"%PYTHON_EXE%" manage.py serve_public
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo [ERROR] Public CMS stopped with exit code %EXIT_CODE%.
)

:finish
echo.
echo [INFO] Launcher exit code: %EXIT_CODE%.
echo [INFO] Press any key to close this window.
pause >nul
exit /b %EXIT_CODE%
