@echo off
chcp 65001 >nul 2>&1
title SWJTU Campus Forum Portable
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0start-portable.ps1"
echo.
echo Press any key to close this window...
pause >nul
