$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $root "start-backend.ps1")
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $root "start-frontend.ps1")

Write-Host "Backend starting at http://127.0.0.1:8000"
Write-Host "Frontend starting at http://127.0.0.1:5173"
Write-Host "Open http://127.0.0.1:5173 in your browser."
