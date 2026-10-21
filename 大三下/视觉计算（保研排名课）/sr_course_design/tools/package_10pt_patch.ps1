param(
    [switch]$IncludeBenchmarkData
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$DistDir = Join-Path $ProjectRoot "dist"
$BuildDir = Join-Path $DistDir "_sr_10pt_patch_build"
$PatchZip = Join-Path $DistDir "sr_10pt_experiment_patch.zip"
$BenchmarkZip = Join-Path $DistDir "sr_benchmark_data_pack.zip"

New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
if (Test-Path $BuildDir) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

function Copy-ProjectFile {
    param([string]$RelativePath)
    $Source = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path $Source)) {
        Write-Host "Skip missing: $RelativePath"
        return
    }
    $Destination = Join-Path $BuildDir $RelativePath
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

$Files = @(
    "run_10pt_experiments_windows.ps1",
    "README_10PT_EXPERIMENTS.md",
    "EXPERIMENTS_10PT.md",
    "CHECKLIST_10PT.md",
    "src/train.py",
    "src/infer.py",
    "src/eval.py",
    "src/models/imdn.py",
    "src/configs/imdn_x2_no_edge_50ep.yaml",
    "tools/prepare_benchmarks.py",
    "tools/evaluate_perceptual_metrics.py",
    "tools/summarize_benchmarks.py",
    "tools/run_benchmark_eval.py",
    "tools/generate_report_assets.py",
    "tools/generate_feature_maps.py",
    "tools/package_10pt_patch.ps1",
    "report/main_report.tex",
    "report/mybib.bib",
    "report/main_report.pdf",
    "logs/imdn_x2_no_edge_50ep_metrics.csv",
    "results_10pt/div2k/bicubic_x2_eval_metrics.csv",
    "results_10pt/div2k/imdn_no_edge_50ep_x2_eval_metrics.csv",
    "results_10pt/benchmarks/benchmark_summary.csv",
    "results_10pt/benchmarks/benchmark_summary.md",
    "results_10pt/perceptual/perceptual_summary.csv"
)

foreach ($File in $Files) {
    Copy-ProjectFile $File
}

$FigureNames = @(
    "full_training_curve_50ep.png",
    "benchmark_visual_grid.png",
    "perceptual_metric_bar.png",
    "dataset_pair_grid.png",
    "imdn_feature_maps.png",
    "training_curves.png",
    "metric_bar.png",
    "extended_experiment_metrics.png",
    "ca_imdn_early_stop_analysis.png"
)
foreach ($FigureName in $FigureNames) {
    Copy-ProjectFile "report/figures/$FigureName"
}

if (Test-Path $PatchZip) {
    Remove-Item -LiteralPath $PatchZip -Force
}
Compress-Archive -Path (Join-Path $BuildDir "*") -DestinationPath $PatchZip -Force
Write-Host "Created patch package: $PatchZip"

if ($IncludeBenchmarkData) {
    $BenchmarkDir = Join-Path $ProjectRoot "data/benchmarks"
    if (Test-Path $BenchmarkDir) {
        $DataBuildDir = Join-Path $DistDir "_sr_benchmark_data_build"
        if (Test-Path $DataBuildDir) {
            Remove-Item -LiteralPath $DataBuildDir -Recurse -Force
        }
        New-Item -ItemType Directory -Force -Path (Join-Path $DataBuildDir "data") | Out-Null
        Copy-Item -LiteralPath $BenchmarkDir -Destination (Join-Path $DataBuildDir "data") -Recurse -Force
        if (Test-Path $BenchmarkZip) {
            Remove-Item -LiteralPath $BenchmarkZip -Force
        }
        Compress-Archive -Path (Join-Path $DataBuildDir "*") -DestinationPath $BenchmarkZip -Force
        Write-Host "Created benchmark data package: $BenchmarkZip"
        Remove-Item -LiteralPath $DataBuildDir -Recurse -Force
    } else {
        Write-Host "Benchmark data folder not found, skip data package."
    }
}

Remove-Item -LiteralPath $BuildDir -Recurse -Force
