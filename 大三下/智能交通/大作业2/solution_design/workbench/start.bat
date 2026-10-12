@echo off
echo ========================================
echo  Traffic Workbench - Starting...
echo ========================================
echo.

REM Check API key
if "%MIMO_API_KEY%" == "" (
    echo [WARNING] MIMO_API_KEY not set!
    echo AI fusion will not work without it.
    echo.
    echo Set it with: set MIMO_API_KEY=tp-your-key
    echo.
)

echo Starting server at http://127.0.0.1:8765
echo Press Ctrl+C to stop.
echo.
python "%~dp0server.py"
