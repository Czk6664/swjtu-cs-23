$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$expected = @(
    "backend/app.py",
    "backend/requirements.txt",
    "backend/Dockerfile",
    "frontend/static/index.html",
    "frontend/nginx.conf",
    "frontend/Dockerfile",
    "docker-compose.yml",
    "k8s/backend-deployment.yaml",
    "k8s/redis-deployment.yaml",
    "k8s/services.yaml",
    "k8s/configmap.yaml",
    "k8s/secret.yaml",
    "k8s/redis-pvc.yaml",
    "k8s/frontend-configmap.yaml",
    "k8s/frontend-deployment.yaml",
    "k8s/hpa.yaml",
    "spark/sparkapplication.yaml",
    "spark/wordcount.py",
    "spark/analysis.py",
    "spark/performance_compare.py",
    "report/report.md",
    "report/screenshot-checklist.md",
    "report/appendix-template.md"
)

$missing = @()
foreach ($path in $expected) {
    $full = Join-Path $root $path
    if (-not (Test-Path -LiteralPath $full)) {
        $missing += $path
    }
}

if ($missing.Count -gt 0) {
    Write-Host "Missing files:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    exit 1
}

Write-Host "All expected files exist." -ForegroundColor Green
