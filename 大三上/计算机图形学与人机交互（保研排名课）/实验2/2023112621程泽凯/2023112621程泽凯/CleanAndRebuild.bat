@echo off
echo Cleaning IntelliSense cache and build output...
echo.

REM Delete .vs folder (contains IntelliSense cache)
if exist ".vs" (
    echo Deleting .vs folder...
    rmdir /s /q ".vs"
)

REM Delete Debug and Release folders
if exist "Debug" (
    echo Deleting Debug folder...
    rmdir /s /q "Debug"
)

if exist "Release" (
    echo Deleting Release folder...
    rmdir /s /q "Release"
)

if exist "x64" (
    echo Deleting x64 folder...
    rmdir /s /q "x64"
)

echo.
echo Cleanup complete!
echo.
echo Please do the following in Visual Studio:
echo 1. Close and reopen Visual Studio
echo 2. Open the project
echo 3. Click "Build" -^> "Rebuild Solution"
echo.
pause
