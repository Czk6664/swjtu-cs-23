$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found in PATH."
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama was not found in PATH. Install Ollama and restart PowerShell."
}

$models = ollama list
if ($LASTEXITCODE -ne 0) {
    throw "Unable to connect to Ollama. Start Ollama and try again."
}
if (-not ($models | Select-String -SimpleMatch "travelqa")) {
    throw "Ollama model 'travelqa' was not found. Import the GGUF model first."
}

Write-Host "[travelqa] Ollama model: travelqa" -ForegroundColor Green
Write-Host "[travelqa] Web UI: http://127.0.0.1:8001" -ForegroundColor Green
python .\scripts\serve.py
