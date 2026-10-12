param(
    [string]$Python = "python",
    [string]$Stage = "all",
    [switch]$DryRun,
    [switch]$SkipTraining,
    [switch]$SkipPerceptual,
    [switch]$SkipReport
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$env:PYTHONUTF8 = "1"

function Invoke-Step {
    param(
        [string]$Label,
        [string]$Command,
        [string[]]$Arguments
    )

    Write-Host ""
    Write-Host "========== $Label =========="
    Write-Host "$Command $($Arguments -join ' ')"
    if ($DryRun) {
        return
    }
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Label"
    }
}

function Invoke-Python {
    param(
        [string]$Label,
        [string[]]$Arguments
    )
    Invoke-Step -Label $Label -Command $Python -Arguments $Arguments
}

function Invoke-XeLaTeX {
    param([string]$Pass)
    if (-not (Get-Command xelatex -ErrorAction SilentlyContinue)) {
        Write-Host "xelatex not found, skip PDF compilation."
        return
    }
    Invoke-Step -Label "Compile report $Pass" -Command "xelatex" -Arguments @(
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-output-directory=.",
        "main_report.tex"
    )
}

New-Item -ItemType Directory -Force -Path "results_10pt", "results_10pt\benchmarks", "results_10pt\div2k", "results_10pt\perceptual", "logs", "checkpoints" | Out-Null

if ($Stage -eq "smoke") {
    Invoke-Python -Label "MindSpore smoke test" -Arguments @("src/smoke_test_ms.py")
    Invoke-Python -Label "Pytest smoke tests" -Arguments @("-m", "pytest", "tests/test_models.py", "tests/test_infer_smoke.py", "-q")
    Invoke-Python -Label "Benchmark prepare smoke" -Arguments @("tools/prepare_benchmarks.py", "--names", "Set5", "--scale", "2", "--skip-existing")
    Write-Host ""
    Write-Host "Smoke stage finished."
    exit 0
}

Invoke-Python -Label "Prepare benchmarks" -Arguments @(
    "tools/prepare_benchmarks.py",
    "--names", "Set5", "Set14", "BSD100", "Urban100",
    "--scale", "2",
    "--skip-existing"
)

if (-not $SkipTraining) {
    Invoke-Python -Label "Train IMDN no-edge 50ep" -Arguments @(
        "-m", "src.train",
        "src/configs/imdn_x2_no_edge_50ep.yaml"
    )
}

$BestCheckpoint = "checkpoints/imdn_no_edge_50ep_x2_best_psnr.ckpt"
$FinalCheckpoint = "checkpoints/imdn_no_edge_50ep_x2.ckpt"
if (-not $DryRun) {
    if (Test-Path $BestCheckpoint) {
        Write-Host "Using best checkpoint: $BestCheckpoint"
    } elseif (Test-Path $FinalCheckpoint) {
        $BestCheckpoint = $FinalCheckpoint
        Write-Host "Best checkpoint not found; using final checkpoint: $BestCheckpoint"
    } else {
        throw "No IMDN 50ep checkpoint found. Expected $BestCheckpoint or $FinalCheckpoint."
    }
}

Invoke-Python -Label "DIV2K inference: Bicubic" -Arguments @(
    "-m", "src.infer",
    "--model", "bicubic",
    "--scale", "2",
    "--input", "./data/eval/LR",
    "--output", "./results_10pt/div2k/bicubic_x2_eval"
)
Invoke-Python -Label "DIV2K eval: Bicubic" -Arguments @(
    "-m", "src.eval",
    "--results", "./results_10pt/div2k/bicubic_x2_eval",
    "--targets", "./data/eval/HR",
    "--scale", "2",
    "--csv", "./results_10pt/div2k/bicubic_x2_eval_metrics.csv"
)
Invoke-Python -Label "DIV2K inference: IMDN 50ep best" -Arguments @(
    "-m", "src.infer",
    "--model", "imdn",
    "--scale", "2",
    "--num-features", "32",
    "--checkpoint", $BestCheckpoint,
    "--input", "./data/eval/LR",
    "--output", "./results_10pt/div2k/imdn_no_edge_50ep_x2_eval"
)
Invoke-Python -Label "DIV2K eval: IMDN 50ep best" -Arguments @(
    "-m", "src.eval",
    "--results", "./results_10pt/div2k/imdn_no_edge_50ep_x2_eval",
    "--targets", "./data/eval/HR",
    "--scale", "2",
    "--csv", "./results_10pt/div2k/imdn_no_edge_50ep_x2_eval_metrics.csv"
)

foreach ($Benchmark in @("Set5", "Set14", "BSD100", "Urban100")) {
    $BenchmarkRoot = "data/benchmarks/$Benchmark"
    if (-not $DryRun -and -not (Test-Path "$BenchmarkRoot/LR")) {
        Write-Host "Skip $Benchmark because $BenchmarkRoot/LR does not exist."
        continue
    }
    Invoke-Python -Label "Benchmark ${Benchmark}: Bicubic" -Arguments @(
        "tools/run_benchmark_eval.py",
        "--benchmark-root", $BenchmarkRoot,
        "--name", $Benchmark,
        "--model", "bicubic",
        "--scale", "2",
        "--output-root", "./results_10pt/benchmarks"
    )
    Invoke-Python -Label "Benchmark ${Benchmark}: IMDN 50ep best" -Arguments @(
        "tools/run_benchmark_eval.py",
        "--benchmark-root", $BenchmarkRoot,
        "--name", $Benchmark,
        "--model", "imdn",
        "--scale", "2",
        "--num-features", "32",
        "--checkpoint", $BestCheckpoint,
        "--output-root", "./results_10pt/benchmarks"
    )
}

Invoke-Python -Label "Summarize benchmarks" -Arguments @(
    "tools/summarize_benchmarks.py",
    "--input-root", "./results_10pt/benchmarks",
    "--output-csv", "./results_10pt/benchmarks/benchmark_summary.csv",
    "--output-md", "./results_10pt/benchmarks/benchmark_summary.md"
)

if (-not $SkipPerceptual) {
    Invoke-Python -Label "Evaluate LPIPS and NIQE" -Arguments @(
        "tools/evaluate_perceptual_metrics.py",
        "--target", "./data/eval/HR",
        "--scale", "2",
        "--result", "Bicubic=./results_10pt/div2k/bicubic_x2_eval",
        "--result", "IMDN50=./results_10pt/div2k/imdn_no_edge_50ep_x2_eval",
        "--output", "./results_10pt/perceptual/perceptual_metrics.csv",
        "--summary", "./results_10pt/perceptual/perceptual_summary.csv"
    )
}

Invoke-Python -Label "Generate report figures" -Arguments @("tools/generate_report_assets.py")

if (-not $SkipReport) {
    Push-Location "report"
    try {
        Invoke-XeLaTeX -Pass "pass 1"
        if (Get-Command bibtex -ErrorAction SilentlyContinue) {
            Invoke-Step -Label "BibTeX" -Command "bibtex" -Arguments @("main_report")
        }
        Invoke-XeLaTeX -Pass "pass 2"
        Invoke-XeLaTeX -Pass "pass 3"
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "10pt experiment flow finished."
Write-Host "Bring these back for final report integration:"
Write-Host "- results_10pt/"
Write-Host "- checkpoints/imdn_no_edge_50ep_x2_best_psnr.ckpt"
Write-Host "- checkpoints/imdn_no_edge_50ep_x2.ckpt"
Write-Host "- logs/imdn_x2_no_edge_50ep_metrics.csv"
