@echo off
echo ============================================================
echo   Cache Memory Simulator  --  Startup Script
echo ============================================================
echo.

set "PYTHON=C:\Users\Usha Sri\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe"
set "SITE_PKG=%~dp0site-packages"
set "BACKEND=%~dp0backend\app.py"

if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON%
    echo Please install Python and update this script.
    pause
    exit /b 1
)

echo [1] Python found: %PYTHON%

cd /d "%~dp0"

echo [2] Starting Flask backend on http://127.0.0.1:5000 ...
echo     Open your browser to: http://127.0.0.1:5000
echo     Press Ctrl+C to stop the server.
echo.

"%PYTHON%" "%BACKEND%"

pause
