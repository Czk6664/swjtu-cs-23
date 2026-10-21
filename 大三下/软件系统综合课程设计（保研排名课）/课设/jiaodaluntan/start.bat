@echo off
chcp 65001 >nul 2>&1
title SWJTU Campus Forum - Starting...
echo.
echo   ========================================
echo     SWJTU Campus Forum - One-Click Start
echo   ========================================
echo.
echo   Starting, please wait...
echo   (First launch may take 1-2 minutes)
echo.
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0start.ps1"
echo.
echo   Press any key to close this window...
pause >nul
