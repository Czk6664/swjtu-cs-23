@echo off
echo ========================================
echo 启动交大校园论坛后端
echo ========================================
echo.

cd /d %~dp0

echo 正在启动后端服务...
echo.

call mvn clean spring-boot:run

pause
