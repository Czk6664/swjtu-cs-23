$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found in PATH. Install Python 3.10+ and restart PowerShell."
}

Write-Host "[semantic-rag] Installing Python dependencies..." -ForegroundColor Cyan
python -m pip install -r .\requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed with exit code $LASTEXITCODE"
}

Write-Host "[semantic-rag] Importing reviewed regulation files..." -ForegroundColor Cyan
python .\scripts\import_regulations.py
if ($LASTEXITCODE -ne 0) {
    throw "Regulation import failed with exit code $LASTEXITCODE"
}

Write-Host "[semantic-rag] Downloading safetensors models from ModelScope..." -ForegroundColor Cyan
python .\scripts\download_rag_models_modelscope.py
if ($LASTEXITCODE -ne 0) {
    throw "ModelScope download failed with exit code $LASTEXITCODE"
}

Write-Host "[semantic-rag] Building semantic knowledge base..." -ForegroundColor Cyan
python .\scripts\2_build_kb.py
if ($LASTEXITCODE -ne 0) {
    throw "Knowledge-base build failed with exit code $LASTEXITCODE"
}

Write-Host "[semantic-rag] Running retrieval smoke test..." -ForegroundColor Cyan
python .\scripts\test_semantic_rag.py
if ($LASTEXITCODE -ne 0) {
    throw "Semantic RAG smoke test failed with exit code $LASTEXITCODE"
}

Write-Host "[semantic-rag] Complete. Start the Web app with: .\start_web.ps1" -ForegroundColor Green
