# Environment Check Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SWJTU Campus Forum - Environment Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Java
Write-Host "Checking Java..." -ForegroundColor Yellow
try {
    $javaVersion = java -version 2>&1 | Select-String "version"
    Write-Host "[OK] Java installed: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Java not installed or not in PATH" -ForegroundColor Red
}
Write-Host ""

# Check Maven
Write-Host "Checking Maven..." -ForegroundColor Yellow
try {
    $mavenVersion = mvn -version 2>&1 | Select-String "Apache Maven"
    Write-Host "[OK] Maven installed: $mavenVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Maven not installed" -ForegroundColor Red
    Write-Host "  Install: choco install maven" -ForegroundColor Gray
}
Write-Host ""

# Check MySQL service
Write-Host "Checking MySQL service..." -ForegroundColor Yellow
$mysqlService = Get-Service -Name MySQL* -ErrorAction SilentlyContinue
if ($mysqlService) {
    if ($mysqlService.Status -eq 'Running') {
        Write-Host "[OK] MySQL running: $($mysqlService.Name)" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] MySQL not running: $($mysqlService.Name)" -ForegroundColor Red
        Write-Host "  Start: Start-Service -Name $($mysqlService.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "[FAIL] MySQL service not found" -ForegroundColor Red
}
Write-Host ""

# Check MySQL CLI
Write-Host "Checking MySQL CLI..." -ForegroundColor Yellow
try {
    $mysqlCmd = Get-Command mysql -ErrorAction Stop
    Write-Host "[OK] MySQL CLI available: $($mysqlCmd.Source)" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] MySQL CLI not in PATH" -ForegroundColor Red
    Write-Host "  Possible locations:" -ForegroundColor Gray
    Write-Host "  - C:\Program Files\MySQL\MySQL Server 8.0\bin" -ForegroundColor Gray
}
Write-Host ""

# Check Redis
Write-Host "Checking Redis..." -ForegroundColor Yellow
$redisService = Get-Service -Name Redis -ErrorAction SilentlyContinue
if ($redisService) {
    if ($redisService.Status -eq 'Running') {
        Write-Host "[OK] Redis running" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Redis not running (optional)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] Redis not installed (optional)" -ForegroundColor Yellow
}
Write-Host ""

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "[OK] Node.js installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Node.js not installed" -ForegroundColor Red
}
Write-Host ""

# Check frontend deps
Write-Host "Checking frontend deps..." -ForegroundColor Yellow
if (Test-Path "frontend/node_modules") {
    Write-Host "[OK] node_modules exists" -ForegroundColor Green
} else {
    Write-Host "[FAIL] node_modules missing" -ForegroundColor Red
    Write-Host "  Run: cd frontend; npm install" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Environment check complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. If Maven missing: choco install maven" -ForegroundColor White
Write-Host "2. If MySQL not running: Start-Service -Name MySQL80" -ForegroundColor White
Write-Host "3. Start backend: cd backend; mvn spring-boot:run" -ForegroundColor White
Write-Host "4. Start frontend: cd frontend; npm install; npm run dev" -ForegroundColor White
Write-Host ""
