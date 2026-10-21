@echo off
echo Cleaning solution...
msbuild WindowsProject2.vcxproj /t:Clean /p:Configuration=Debug /p:Platform=x64

echo Deleting IntelliSense cache...
if exist .vs rmdir /s /q .vs
if exist x64\Debug rmdir /s /q x64\Debug

echo Rebuilding solution...
msbuild WindowsProject2.vcxproj /t:Rebuild /p:Configuration=Debug /p:Platform=x64

echo Done!
pause
