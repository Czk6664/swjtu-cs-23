$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$webDir = Join-Path $root "apps\web"

Write-Host "Starting frontend in $webDir"
Set-Location $webDir

if (-not (Test-Path "node_modules")) {
  Write-Host "Installing frontend dependencies..."
  npm install
}

npm run dev -- --host 127.0.0.1 --port 5173
