@echo off
set JAVA_HOME=D:\ruanjian\IntelliJ IDEA 2025.3.3\jbr
cd /d "%~dp0"
echo Compiling with Java 21...
"%JAVA_HOME%\bin\java.exe" -version
mvn clean compile -Dmaven.compiler.fork=true -Dmaven.compiler.executable="%JAVA_HOME%\bin\javac.exe"
echo.
echo Done!
pause
