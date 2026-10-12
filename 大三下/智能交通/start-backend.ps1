$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiDir = Join-Path $root "services\api"

Write-Host "Starting backend in $apiDir"
Set-Location $apiDir

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  Write-Host "Creating Python virtual environment..."
  python -m venv .venv
  & ".venv\Scripts\python.exe" -m pip install -e .
}

& ".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
