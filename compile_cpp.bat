@echo off
echo ============================================================
echo   Cache Memory Simulator  --  Compile C++ Engine
echo   (requires g++ / MinGW on PATH)
echo ============================================================
echo.

set "CPP_DIR=%~dp0cpp"
set "OUT=%CPP_DIR%\cache_sim.exe"

cd /d "%CPP_DIR%"

where g++ >nul 2>&1
if errorlevel 1 (
    echo WARNING: g++ not found on PATH.
    echo The simulator will use the Python engine instead.
    echo To use the C++ engine, install MinGW-w64 and add it to PATH.
    pause
    exit /b 1
)

echo Compiling C++ simulation engine...
g++ -std=c++17 -O2 -o "%OUT%" main.cpp

if errorlevel 1 (
    echo ERROR: Compilation failed.
    pause
    exit /b 1
)

echo SUCCESS: Compiled to %OUT%
echo The Flask backend will now use the C++ engine automatically.
pause
