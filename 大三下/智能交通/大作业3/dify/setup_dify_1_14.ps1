$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ZipPath = Join-Path $ProjectRoot "dify-1.14.2.zip"
$ExtractedDifyRoot = Join-Path $ProjectRoot "dify-1.14.2\dify-1.14.2"
$RuntimeDir = Join-Path $ProjectRoot ".runtime"
$DifyRoot = if (Test-Path -LiteralPath (Join-Path $ExtractedDifyRoot "docker\docker-compose.yaml")) {
    $ExtractedDifyRoot
} else {
    Join-Path $RuntimeDir "dify-1.14.2"
}
$DockerDir = Join-Path $DifyRoot "docker"

if (-not (Test-Path -LiteralPath $DockerDir) -and -not (Test-Path -LiteralPath $ZipPath)) {
    throw "Missing Dify source archive: $ZipPath"
}

New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

if (-not (Test-Path -LiteralPath $DockerDir)) {
    Write-Host "[dify] Extracting $ZipPath ..."
    tar.exe -xf $ZipPath -C $RuntimeDir
}

if (-not (Test-Path -LiteralPath $DockerDir)) {
    throw "Dify docker directory not found: $DockerDir"
}

$EnvExample = Join-Path $DockerDir ".env.example"
$EnvFile = Join-Path $DockerDir ".env"
if (-not (Test-Path -LiteralPath $EnvFile)) {
    Copy-Item -LiteralPath $EnvExample -Destination $EnvFile
    Write-Host "[dify] Created docker .env from .env.example"
}

Write-Host "[dify] Starting Dify 1.14.2 with Docker Compose ..."
Push-Location $DockerDir
try {
    docker compose up -d
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "[dify] Open: http://localhost"
Write-Host "[travelqa] In another PowerShell, start tool service:"
Write-Host "  cd `"$ProjectRoot`""
Write-Host "  .\start_web.ps1"
Write-Host ""
Write-Host "[dify] Import custom API tool from:"
Write-Host "  $PSScriptRoot\travelqa-tools.openapi.yaml"
