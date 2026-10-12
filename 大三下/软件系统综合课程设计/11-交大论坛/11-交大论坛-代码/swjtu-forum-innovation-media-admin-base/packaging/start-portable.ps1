param(
    [int]$BackendPort = 8080,
    [int]$FrontendPort = 4173
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$BundledJava = Join-Path $Root 'runtime\bin\java.exe'
$Java = if (Test-Path $BundledJava) { $BundledJava } else { 'java' }
$BackendJar = Join-Path $Root 'app\backend\forum-1.0.0.jar'
$PrimaryFrontendJar = Join-Path $Root 'app\frontend-server.jar'
$LegacyFrontendJar = Join-Path $Root 'app\tools\frontend-server.jar'
$FrontendJar = if (Test-Path $PrimaryFrontendJar) { $PrimaryFrontendJar } else { $LegacyFrontendJar }
$FrontendDist = Join-Path $Root 'app\frontend\dist'
$BackendDir = Join-Path $Root 'app\backend'

function Write-Step([string]$msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok([string]$msg) { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Err([string]$msg) { Write-Host "    [ERR] $msg" -ForegroundColor Red }

function Clear-Port([int]$Port) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
    } catch {
        Write-Ok "Port $Port is free"
        return
    }
    foreach ($procId in ($connections | Select-Object -ExpandProperty OwningProcess -Unique)) {
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            if ($proc.ProcessName -match '^(java|javaw)$') {
                Stop-Process -Id $procId -Force
                Write-Ok "Stopped $($proc.ProcessName) on port $Port"
            }
        } catch { }
    }
}

function Wait-Url([string]$Url, [int]$Seconds) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) { return $true }
        } catch { }
        Start-Sleep -Seconds 2
    }
    return $false
}

Write-Host "SWJTU Campus Forum Portable" -ForegroundColor Magenta
if (Test-Path $BundledJava) {
    Write-Host "This package uses bundled Java runtime: $Java" -ForegroundColor DarkGray
} else {
    Write-Host "Bundled Java runtime not found; falling back to system Java on PATH." -ForegroundColor DarkGray
}

if (-not (Test-Path $BundledJava)) {
    try {
        $null = & java -version 2>&1
    } catch {
        Write-Err "Java not found. Install Java 17+ or use the no-external-java package with bundled runtime."
        exit 1
    }
}
if (-not (Test-Path $BackendJar)) { Write-Err "Backend jar not found: $BackendJar"; exit 1 }
if (-not (Test-Path $FrontendJar)) { Write-Err "Frontend server jar not found: $FrontendJar"; exit 1 }
if (-not (Test-Path $FrontendDist)) { Write-Err "Frontend dist not found: $FrontendDist"; exit 1 }

Write-Step "Freeing ports"
Clear-Port $BackendPort
Clear-Port $FrontendPort

New-Item -ItemType Directory -Force (Join-Path $BackendDir 'logs') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $BackendDir 'data') | Out-Null

Write-Step "Starting backend"
$backendArgs = @(
    '-Dfile.encoding=UTF-8',
    '--enable-native-access=ALL-UNNAMED',
    '-jar', $BackendJar,
    '--spring.profiles.active=demo',
    "--server.port=$BackendPort"
)
$backend = Start-Process -FilePath $Java -ArgumentList $backendArgs -WorkingDirectory $BackendDir -PassThru -WindowStyle Hidden
Write-Ok "Backend PID: $($backend.Id)"

Write-Step "Starting frontend static server"
$frontendArgs = @(
    '-Dfile.encoding=UTF-8',
    '-jar', $FrontendJar,
    $FrontendDist,
    $FrontendPort,
    $BackendPort
)
$frontend = Start-Process -FilePath $Java -ArgumentList $frontendArgs -WorkingDirectory $Root -PassThru -WindowStyle Hidden
Write-Ok "Frontend PID: $($frontend.Id)"

Write-Step "Waiting for services"
$backendReady = Wait-Url "http://localhost:$BackendPort/api/sections" 90
$frontendReady = Wait-Url "http://localhost:$FrontendPort" 30

Write-Host "`n============================================================" -ForegroundColor Magenta
if ($backendReady -and $frontendReady) {
    Write-Host "Services are ready." -ForegroundColor Green
} else {
    Write-Host "Services may still be starting. If the page is blank, wait and refresh." -ForegroundColor Yellow
}
Write-Host "Frontend: http://localhost:$FrontendPort"
Write-Host "Backend : http://localhost:$BackendPort/api"
Write-Host "Admin access is available from the forum navigation after signing in."
Write-Host "============================================================" -ForegroundColor Magenta

try {
    Start-Process "http://localhost:$FrontendPort"
} catch { }

Write-Host "`nKeep this window open while using the system."
Write-Host "Press Ctrl+C to stop, or close this window and run stop-portable.bat."
while ($true) {
    Start-Sleep -Seconds 2
    if ($backend.HasExited -or $frontend.HasExited) {
        Write-Host "A service exited. Backend exited=$($backend.HasExited), Frontend exited=$($frontend.HasExited)" -ForegroundColor Yellow
        break
    }
}
