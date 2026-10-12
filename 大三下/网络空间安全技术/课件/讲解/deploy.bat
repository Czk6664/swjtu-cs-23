@echo off
chcp 65001 >nul
cls
echo.
echo ========================================
echo   Deploy NetSec Study Site to Cloudflare
echo ========================================
echo.

set project_name=netsec-study

echo [1/3] Checking login status...
call wrangler whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [!] You are NOT logged in to Cloudflare.
    echo     Opening login page in browser...
    echo.
    call wrangler login
    if %errorlevel% neq 0 (
        echo [ERROR] Login failed. Please run: wrangler login
        pause
        exit /b 1
    )
)

echo.
echo [2/3] Uploading files to Cloudflare Pages...
echo Project: %project_name%
echo Directory: %cd%
echo.

call wrangler pages deploy . --project-name=%project_name%

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo [ERROR] Deploy failed!
    echo ========================================
    echo Possible reasons:
    echo   1. Not logged in   -^> run: wrangler login
    echo   2. Network / API issue
    echo   3. Project name taken -^> change project_name in this file
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS!
echo ========================================
echo.
echo Your study site is now live at:
echo   https://%project_name%.pages.dev
echo.
echo Tip: press Ctrl+F5 to force refresh.
echo To update later: just run this script again.
echo.
pause
