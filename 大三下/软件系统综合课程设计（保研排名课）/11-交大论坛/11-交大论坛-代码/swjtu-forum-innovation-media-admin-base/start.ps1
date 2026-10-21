<#
.SYNOPSIS
    SWJTU Campus Forum - One-Click Launcher

.DESCRIPTION
    1. Free ports 8080 / 4173 (kill stale java/node processes)
    2. Start backend (java -jar when a built jar exists; otherwise build it)
    3. Build frontend dist when needed, then start Vite preview
    4. Poll backend readiness, then print access URLs and default account

.PARAMETER BackendPort
    Backend port, default 8080.

.PARAMETER FrontendPort
    Frontend port, default 4173.

.EXAMPLE
    .\start.ps1
#>

param(
    [int]$BackendPort = 8080,
    [int]$FrontendPort = 4173,
    [string]$SpringProfile = 'mysql'
)

$ErrorActionPreference = 'Stop'

$RepoRoot     = $PSScriptRoot
$BackendDir   = Join-Path $RepoRoot 'backend'
$FrontendDir  = Join-Path $RepoRoot 'frontend'
$FrontendDist = Join-Path $FrontendDir 'dist'

$ReadyTimeoutSeconds = 120
$ReadyPollSeconds    = 2

function Write-Step  ([string]$msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok    ([string]$msg) { Write-Host "    [OK]   $msg" -ForegroundColor Green }
function Write-Warn2 ([string]$msg) { Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function Write-Err2  ([string]$msg) { Write-Host "    [ERR]  $msg" -ForegroundColor Red }

function Clear-Port {
    param([int]$Port)
    $conns = $null
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
    } catch {
        Write-Ok "Port $Port is free"
        return
    }
    if (-not $conns) { Write-Ok "Port $Port is free"; return }
    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        if (-not $procId -or $procId -eq 0) { continue }
        try { $proc = Get-Process -Id $procId -ErrorAction Stop } catch { continue }
        $name = $proc.ProcessName
        if ($name -match '^(java|javaw|node)$') {
            Write-Warn2 "Port $Port occupied by $name (PID $procId), killing..."
            try { Stop-Process -Id $procId -Force -ErrorAction Stop; Write-Ok "Killed $name (PID $procId)" }
            catch { Write-Err2 "Failed to kill PID $procId : $($_.Exception.Message)" }
        } else {
            Write-Warn2 "Port $Port occupied by non-java/node process $name (PID $procId), skipped."
        }
    }
}

function Wait-BackendReady {
    param([int]$Port, [int]$TimeoutSeconds, [int]$PollSeconds)
    $url = "http://localhost:$Port/api/sections"
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    Write-Step "Waiting for backend: $url (timeout ${TimeoutSeconds}s)"
    while ((Get-Date) -lt $deadline) {
        try {
            $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { Write-Ok "Backend ready (HTTP 200)"; return $true }
        } catch { }
        Start-Sleep -Seconds $PollSeconds
        Write-Host "    ... not ready yet, waiting" -ForegroundColor DarkGray
    }
    Write-Err2 "Timeout (${TimeoutSeconds}s). Backend did not start. Check the backend window for errors."
    return $false
}

function Resolve-BackendJar {
    $candidates = @(
        (Join-Path $BackendDir 'target\forum-1.0.0.jar'),
        (Join-Path $BackendDir 'forum-1.0.0.jar'),
        (Join-Path $RepoRoot 'release\swjtu-forum-portable\app\backend\forum-1.0.0.jar')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    return $null
}

function Test-BackendBuildRequired {
    param([string]$JarPath)
    if (-not $JarPath -or -not (Test-Path $JarPath)) {
        return $true
    }
    $jarTime = (Get-Item $JarPath).LastWriteTime
    $latestSource = Get-ChildItem -Path $BackendDir -Recurse -File `
        -Include *.java,*.yml,*.yaml,*.properties,*.xml |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    return ($latestSource -and $latestSource.LastWriteTime -gt $jarTime)
}

# ===========================================================================
# Main
# ===========================================================================
Write-Host "SWJTU Campus Forum - One-Click Launcher" -ForegroundColor Magenta
Write-Host "Backend port = $BackendPort  Frontend port = $FrontendPort  Profile = $SpringProfile" -ForegroundColor Magenta
if ($SpringProfile -eq 'mysql') {
    Write-Host "MySQL mode: set DB_USERNAME / DB_PASSWORD / DB_URL before launch when needed." -ForegroundColor Yellow
    Write-Host "Default DB_URL = jdbc:mysql://localhost:3306/swjtu_forum" -ForegroundColor Yellow
}

if (-not (Test-Path $BackendDir))  { Write-Err2 "Backend dir not found: $BackendDir"; exit 1 }
if (-not (Test-Path $FrontendDir)) { Write-Err2 "Frontend dir not found: $FrontendDir"; exit 1 }

# Step 1: Free ports
Write-Step "Freeing ports"
Clear-Port -Port $BackendPort
Clear-Port -Port $FrontendPort

# Step 2: Check frontend deps
$NodeModules = Join-Path $FrontendDir 'node_modules'
if (-not (Test-Path $NodeModules)) {
    Write-Step "node_modules missing, running npm install (may take a few minutes)"
    Push-Location $FrontendDir
    try {
        npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install failed (exit code $LASTEXITCODE)" }
        Write-Ok "npm install done"
    } catch {
        Write-Err2 $_.Exception.Message
        Pop-Location
        exit 1
    }
    Pop-Location
} else {
    Write-Ok "node_modules exists, skipping npm install"
}

# Step 3: Build backend jar when missing or stale
$JarFile = Resolve-BackendJar
if (Test-BackendBuildRequired -JarPath $JarFile) {
    if ($JarFile) {
        Write-Step "Backend source changed after jar build, rebuilding with Maven"
    } else {
        Write-Step "Backend jar missing, building with Maven"
    }
    Push-Location $BackendDir
    try {
        mvn -DskipTests package
        if ($LASTEXITCODE -ne 0) { throw "Maven package failed (exit code $LASTEXITCODE)" }
    } catch {
        Write-Err2 $_.Exception.Message
        Pop-Location
        exit 1
    }
    Pop-Location
    $JarFile = Resolve-BackendJar
}
if (-not $JarFile) { Write-Err2 "Backend jar still not found after build"; exit 1 }
Write-Ok "Using backend jar: $JarFile"

# Step 4: Always rebuild frontend dist to avoid stale hashed assets in portable runs
Write-Step "Building frontend dist"
Push-Location $FrontendDir
try {
    if (Test-Path $FrontendDist) {
        $resolvedDist = (Resolve-Path $FrontendDist).Path
        if (-not $resolvedDist.StartsWith($FrontendDir)) {
            throw "Refuse to clean unexpected dist path: $resolvedDist"
        }
        Remove-Item -LiteralPath $resolvedDist -Recurse -Force
    }
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build failed (exit code $LASTEXITCODE)" }
} catch {
    Write-Err2 $_.Exception.Message
    Pop-Location
    exit 1
}
Pop-Location

# Step 5: Start backend (java -jar)
Write-Step "Starting backend (java -jar, port $BackendPort, profile $SpringProfile)"
$env:JAVA_TOOL_OPTIONS = "-Dfile.encoding=UTF-8"
$backendProc = Start-Process -FilePath 'java' `
    -ArgumentList @('-Dfile.encoding=UTF-8', "-Dspring.profiles.active=$SpringProfile", '-jar', $JarFile, "--server.port=$BackendPort") `
    -WorkingDirectory $BackendDir `
    -PassThru
if ($backendProc) {
    Write-Ok "Backend started (PID $($backendProc.Id))"
} else {
    Write-Err2 "Backend failed to start"
    exit 1
}

# Step 6: Start frontend (vite preview)
Write-Step "Starting frontend (vite preview, port $FrontendPort, proxy -> backend $BackendPort)"
$frontendCmd = "`$env:BACKEND_PORT=$BackendPort; npm run preview -- --port $FrontendPort"
$frontendProc = Start-Process -FilePath 'powershell.exe' `
    -ArgumentList '-NoExit', '-Command', $frontendCmd `
    -WorkingDirectory $FrontendDir `
    -PassThru
if ($frontendProc) {
    Write-Ok "Frontend started (PID $($frontendProc.Id))"
} else {
    Write-Err2 "Frontend failed to start"
}

# Step 7: Wait for backend
$ready = Wait-BackendReady -Port $BackendPort -TimeoutSeconds $ReadyTimeoutSeconds -PollSeconds $ReadyPollSeconds

# Step 8: Print access info
Write-Host "`n============================================================" -ForegroundColor Magenta
if ($ready) {
    Write-Host " All services are ready!" -ForegroundColor Green
} else {
    Write-Host " Backend not ready in time. Check the backend window." -ForegroundColor Yellow
}
Write-Host "------------------------------------------------------------"
Write-Host (" Frontend  : http://localhost:{0}" -f $FrontendPort)
Write-Host (" Backend   : http://localhost:{0}/api" -f $BackendPort)
if ($SpringProfile -eq 'demo') {
    Write-Host (" H2 Console: http://localhost:{0}/api/h2-console" -f $BackendPort)
} else {
    Write-Host " Database  : MySQL profile, database name swjtu_forum"
}
Write-Host "------------------------------------------------------------"
Write-Host " Default admin: admin / admin123456" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "`nBackend and frontend run in separate windows."
Write-Host "To stop: close those windows, or run: Get-Process java,node | Stop-Process -Force"

if (-not $ready) { exit 1 }
