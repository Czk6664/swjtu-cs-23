$ErrorActionPreference = 'Stop'
$RepoRoot     = $PSScriptRoot
$BackendDir   = Join-Path $RepoRoot 'backend'
$FrontendDir  = Join-Path $RepoRoot 'frontend'
$FrontendDist = Join-Path $FrontendDir 'dist'
$PackagingDir = Join-Path $RepoRoot 'packaging'
$ReleaseDir   = Join-Path $RepoRoot 'release\swjtu-forum-portable'
$JdkPath      = "C:\Program Files\Java\jdk-17"

function Write-Step([string]$m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Write-Ok([string]$m)   { Write-Host "    [OK]   $m" -ForegroundColor Green }
function Write-Err2([string]$m) { Write-Host "    [ERR]  $m" -ForegroundColor Red }

# Step 1: Build backend JAR
Write-Step "Building backend JAR"
$jarPath = Join-Path $BackendDir 'target\forum-1.0.0.jar'
Push-Location $BackendDir
mvn -DskipTests package
if ($LASTEXITCODE -ne 0) { Write-Err2 "Maven failed"; Pop-Location; exit 1 }
Pop-Location
Write-Ok "Backend JAR built"

# Step 2: Build frontend dist
Write-Step "Building frontend dist"
Push-Location $FrontendDir
if (-not (Test-Path (Join-Path $FrontendDir 'node_modules'))) {
    npm install
    if ($LASTEXITCODE -ne 0) { Write-Err2 "npm install failed"; Pop-Location; exit 1 }
}
if (Test-Path $FrontendDist) {
    $resolvedDist = (Resolve-Path $FrontendDist).Path
    if (-not $resolvedDist.StartsWith($FrontendDir)) {
        Write-Err2 "Refuse to clean unexpected dist path: $resolvedDist"
        Pop-Location
        exit 1
    }
    Remove-Item -LiteralPath $resolvedDist -Recurse -Force
}
npm run build
if ($LASTEXITCODE -ne 0) { Write-Err2 "Frontend build failed"; Pop-Location; exit 1 }
Pop-Location
Write-Ok "Frontend dist built"

# Step 3: Create minimal JRE
Write-Step "Creating minimal JRE"
$JreDir  = Join-Path $ReleaseDir 'runtime'
if (Test-Path $jreDir) {
    Write-Ok "JRE exists"
} else {
    if (-not (Test-Path $JdkPath)) { Write-Err2 "JDK 17 not found"; exit 1 }
    $modules = "java.base,java.desktop,java.instrument,java.logging,java.management,java.naming,java.net.http,java.prefs,java.rmi,java.security.jgss,java.security.sasl,java.sql,java.transaction.xa,java.xml,java.xml.crypto,jdk.unsupported,jdk.crypto.cryptoki,jdk.crypto.ec,jdk.crypto.mscapi"
    $jlinkExe = Join-Path $JdkPath 'bin\jlink.exe'
    & $jlinkExe --module-path (Join-Path $JdkPath 'jmods') --add-modules $modules --strip-debug --no-man-pages --no-header-files --compress=2 --output $jreDir
    if ($LASTEXITCODE -ne 0) { Write-Err2 "jlink failed"; exit 1 }
    Write-Ok "JRE created"
}

# Step 4: Compile FrontendServer
Write-Step "Compiling FrontendServer"
$fsJar = Join-Path $ReleaseDir 'app\frontend-server.jar'
$javacExe = Join-Path $JdkPath 'bin\javac.exe'
$jarExe = Join-Path $JdkPath 'bin\jar.exe'
$tmpC = Join-Path $RepoRoot '.tmp-compile'
if (Test-Path $tmpC) { Remove-Item $tmpC -Recurse -Force }
New-Item -ItemType Directory -Path $tmpC -Force | Out-Null
& $javacExe --source 17 --target 17 -d $tmpC (Join-Path $PackagingDir 'FrontendServer.java')
if ($LASTEXITCODE -ne 0) { Write-Err2 "Compile failed"; exit 1 }
$metaDir = Join-Path $tmpC 'META-INF'
New-Item -ItemType Directory -Path $metaDir -Force | Out-Null
Set-Content -Path (Join-Path $metaDir 'MANIFEST.MF') -Value "Main-Class: FrontendServer`r`n"
Push-Location $tmpC
& $jarExe cfm $fsJar META-INF\MANIFEST.MF FrontendServer.class
Pop-Location
Remove-Item $tmpC -Recurse -Force
Write-Ok "FrontendServer JAR compiled"

# Step 5: Assemble
Write-Step "Assembling package"
$appDir = Join-Path $ReleaseDir 'app'
New-Item -ItemType Directory -Path (Join-Path $appDir 'backend') -Force | Out-Null
Copy-Item $jarPath (Join-Path $appDir 'backend\forum-1.0.0.jar') -Force
Write-Ok "Backend JAR copied"

$destDist = Join-Path $appDir 'frontend\dist'
if (Test-Path $destDist) { Remove-Item $destDist -Recurse -Force }
Copy-Item $FrontendDist $destDist -Recurse -Force
Write-Ok "Frontend dist copied"

# Step 6: Create startup scripts
Write-Step "Creating scripts"

$startContent = @'
@echo off
chcp 65001 >nul 2>&1
title SWJTU Campus Forum Portable
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0start-portable.ps1"
echo.
echo Press any key to close this window...
pause >nul
'@

Set-Content -Path (Join-Path $ReleaseDir 'start.bat') -Value $startContent -Encoding ASCII

Copy-Item (Join-Path $PackagingDir 'start-portable.bat') (Join-Path $ReleaseDir 'start-portable.bat') -Force
Copy-Item (Join-Path $PackagingDir 'start-portable.ps1') (Join-Path $ReleaseDir 'start-portable.ps1') -Force
Copy-Item (Join-Path $PackagingDir 'README-portable.txt') (Join-Path $ReleaseDir 'README.txt') -Force

$stopContent = @'
@echo off
call "%~dp0stop-portable.bat"
'@

Set-Content -Path (Join-Path $ReleaseDir 'stop.bat') -Value $stopContent -Encoding ASCII
Copy-Item (Join-Path $PackagingDir 'stop-portable.bat') (Join-Path $ReleaseDir 'stop-portable.bat') -Force
Copy-Item (Join-Path $PackagingDir 'stop-portable.ps1') (Join-Path $ReleaseDir 'stop-portable.ps1') -Force
Write-Ok "Scripts created"

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Done! Package at: $ReleaseDir" -ForegroundColor Green
Write-Host "  Start: double-click start.bat" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
