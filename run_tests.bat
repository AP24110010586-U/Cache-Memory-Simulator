@echo off
echo ============================================================
echo   Cache Memory Simulator  --  Run ALL Tests
echo ============================================================
echo.

set "PYTHON=C:\Users\Usha Sri\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\python.exe"
set "SITE=%~dp0site-packages"

cd /d "%~dp0"

echo [1] Running Engine Unit Tests...
echo.
set "PYTHONPATH=%SITE%"
"%PYTHON%" tests\test_cache.py
echo.

echo [2] Running Flask API Tests...
echo.
"%PYTHON%" tests\test_api.py
echo.

echo ============================================================
echo   Done! Check results above.
echo ============================================================
pause
