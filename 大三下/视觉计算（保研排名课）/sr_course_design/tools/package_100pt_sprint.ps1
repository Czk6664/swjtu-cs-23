$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Dist = Join-Path $Root "dist"
$PackageRoot = Join-Path $Dist "sr_100pt_sprint_patch"
$ZipPath = Join-Path $Dist "sr_100pt_sprint_patch.zip"

if (Test-Path $PackageRoot) {
    Remove-Item -LiteralPath $PackageRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null
New-Item -ItemType Directory -Force -Path $Dist | Out-Null

function Copy-IfExists {
    param([string]$RelativePath)
    $Source = Join-Path $Root $RelativePath
    if (-not (Test-Path $Source)) { return }
    $Target = Join-Path $PackageRoot $RelativePath
    $TargetParent = Split-Path -Parent $Target
    New-Item -ItemType Directory -Force -Path $TargetParent | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Target -Recurse -Force
}

$Paths = @(
    "src\models\imdn.py",
    "src\infer.py",
    "src\train.py",
    "src\self_ensemble.py",
    "src\configs\idb_imdn_x2_smoke.yaml",
    "src\configs\idb_imdn_x2_20ep.yaml",
    "src\configs\idb_imdn_x2_50ep.yaml",
    "tools\run_self_ensemble_eval.py",
    "tools\summarize_100pt_results.py",
    "tools\generate_100pt_assets.py",
    "tools\run_benchmark_eval.py",
    "tools\count_parameters.py",
    "tools\package_100pt_sprint.ps1",
    "tests\test_models.py",
    "tests\test_self_ensemble.py",
    "run_100pt_sprint_windows.ps1",
    "README_100PT_SPRINT.md",
    "CHECKLIST_100PT.md",
    "report\main_report.tex",
    "report\main_report.pdf",
    "report\main_report_100pt.pdf",
    "openspec\changes\sr-100-point-sprint"
)

foreach ($Path in $Paths) {
    Copy-IfExists $Path
}

foreach ($Figure in @(
    "self_ensemble_metrics.png",
    "self_ensemble_visual_grid.png",
    "idb_imdn_comparison.png"
)) {
    Copy-IfExists "report\figures\$Figure"
}

Copy-IfExists "results_100pt\summaries"

if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
Compress-Archive -Path (Join-Path $PackageRoot "*") -DestinationPath $ZipPath -Force
Write-Host "Created patch package: $ZipPath"
