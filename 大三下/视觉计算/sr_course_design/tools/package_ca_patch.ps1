param(
    [string]$Output = "dist/sr_ca_imdn_experiment_patch.zip"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Stage = Join-Path $Root "dist\ca_imdn_patch_stage"
if (Test-Path $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $Stage | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Stage "code_patch") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Stage "report_patch") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Stage "scripts") | Out-Null

function Copy-Rel {
    param([string]$Rel, [string]$Base = "code_patch")
    $Source = Join-Path $Root $Rel
    if (-not (Test-Path $Source)) {
        return
    }
    $Dest = Join-Path (Join-Path $Stage $Base) $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Dest -Force
}

$CodeFiles = @(
    "src\models\imdn.py",
    "src\train.py",
    "src\infer.py",
    "src\configs\ca_imdn_x2_no_edge_20ep.yaml",
    "src\configs\ca_imdn_x2_no_edge_50ep.yaml",
    "src\configs\ca_imdn_x2_edge_w001_20ep.yaml",
    "src\configs\ca_imdn_x2_smoke.yaml",
    "src\configs\srcnn_x2_20ep.yaml",
    "src\configs\imdn_x2_width16_20ep.yaml",
    "src\configs\imdn_x2_width48_20ep.yaml",
    "src\configs\imdn_x2_depth2_20ep.yaml",
    "src\configs\imdn_x2_depth6_20ep.yaml",
    "src\configs\imdn_x2_no_edge_20ep_step_lr.yaml",
    "src\configs\imdn_x2_no_edge_20ep_cosine_lr.yaml",
    "src\configs\ca_imdn_x2_no_edge_20ep_cosine_lr.yaml",
    "tools\summarize_experiments.py",
    "tools\generate_report_assets.py",
    "tools\analyze_frequency.py",
    "tools\count_parameters.py",
    "tools\run_benchmark_eval.py",
    "tools\package_ca_patch.ps1",
    "tests\test_models.py"
)
foreach ($File in $CodeFiles) { Copy-Rel $File }

Copy-Rel "run_ca_experiments_windows.ps1" "scripts"
Copy-Rel "README_CA_IMDN_PATCH.md" "."
Copy-Rel "EXPERIMENTS_CA_IMDN.md" "."
Copy-Rel "CHECKLIST_CA_IMDN.md" "."

$ReportFiles = @(
    "report\main_report.tex",
    "report\main_report.pdf",
    "report\figures\imdn_feature_maps.png",
    "report\figures\metric_bar.png",
    "report\figures\edge_ablation_metrics.png",
    "report\figures\extended_experiment_metrics.png",
    "report\figures\model_capacity_ablation.png",
    "report\figures\scheduler_ablation.png",
    "report\figures\training_time_comparison.png",
    "report\figures\ca_imdn_early_stop_analysis.png",
    "report\figures\frequency_analysis.png"
)
foreach ($File in $ReportFiles) { Copy-Rel $File "report_patch" }

$MetricFiles = @(
    "results\srcnn_20ep_x2_eval_metrics.csv",
    "results\ca_imdn_no_edge_20ep_x2_eval_metrics.csv",
    "results\ca_imdn_no_edge_50ep_x2_eval_metrics.csv",
    "results\ca_imdn_edge_w001_20ep_x2_eval_metrics.csv",
    "results\ca_imdn_no_edge_20ep_cosine_lr_x2_eval_metrics.csv",
    "results\imdn_width16_20ep_x2_eval_metrics.csv",
    "results\imdn_width48_20ep_x2_eval_metrics.csv",
    "results\imdn_depth2_20ep_x2_eval_metrics.csv",
    "results\imdn_depth6_20ep_x2_eval_metrics.csv",
    "results\imdn_no_edge_20ep_step_lr_x2_eval_metrics.csv",
    "results\imdn_no_edge_20ep_cosine_lr_x2_eval_metrics.csv",
    "results\summaries\experiment_summary_from_run3.csv",
    "results\summaries\experiment_summary_from_run3.md",
    "results\summaries\parameter_counts.csv",
    "results\benchmarks\Set5_bicubic_x2_metrics.csv",
    "results\benchmarks\Set5_imdn_x2_metrics.csv",
    "results\benchmarks\Set14_bicubic_x2_metrics.csv",
    "results\benchmarks\Set14_imdn_x2_metrics.csv"
)
foreach ($File in $MetricFiles) { Copy-Rel $File "report_patch" }

$OutputPath = Join-Path $Root $Output
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
if (Test-Path $OutputPath) {
    Remove-Item -LiteralPath $OutputPath -Force
}
Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $OutputPath -Force
Write-Host "Created patch package: $OutputPath"
