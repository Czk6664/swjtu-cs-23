$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found in PATH. Install Python 3.10+ and restart PowerShell."
}

Write-Host "[setup] Installing Python dependencies..." -ForegroundColor Cyan
python -m pip install -r .\requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed with exit code $LASTEXITCODE"
}

Write-Host "[setup] Testing Amap weather and route APIs..." -ForegroundColor Cyan
python .\scripts\test_amap_tools.py
if ($LASTEXITCODE -ne 0) {
    throw "Amap API test failed with exit code $LASTEXITCODE"
}

Write-Host "[setup] Complete. Start the Web app with: .\start_web.ps1" -ForegroundColor Green
