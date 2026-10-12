param(
    [string]$Python = "python",
    [string]$Stage = "all",
    [switch]$DryRun,
    [string]$BestCheckpoint = ".\checkpoints\imdn_no_edge_50ep_x2_best_psnr.ckpt"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Run-Step {
    param(
        [string]$Label,
        [string[]]$Arguments
    )
    Write-Host ""
    Write-Host "========== $Label =========="
    Write-Host "$Python $($Arguments -join ' ')"
    if ($DryRun) { return }
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Label"
    }
}

function Run-XeLaTeX {
    if ($DryRun) {
        Write-Host "xelatex/bibtex compile report/main_report.tex"
        return
    }
    Push-Location ".\report"
    try {
        & xelatex -interaction=nonstopmode -halt-on-error main_report.tex
        if ($LASTEXITCODE -ne 0) {
            Write-Host "main_report.pdf may be locked. Falling back to main_report_100pt.pdf."
            & xelatex -jobname=main_report_100pt -interaction=nonstopmode -halt-on-error main_report.tex
            if ($LASTEXITCODE -ne 0) { throw "xelatex failed for main_report_100pt" }
            & bibtex main_report_100pt
            if ($LASTEXITCODE -ne 0) { throw "bibtex failed for main_report_100pt" }
            & xelatex -jobname=main_report_100pt -interaction=nonstopmode -halt-on-error main_report.tex
            if ($LASTEXITCODE -ne 0) { throw "xelatex rerun failed for main_report_100pt" }
            & xelatex -jobname=main_report_100pt -interaction=nonstopmode -halt-on-error main_report.tex
            if ($LASTEXITCODE -ne 0) { throw "final xelatex rerun failed for main_report_100pt" }
            return
        }
        & bibtex main_report
        if ($LASTEXITCODE -ne 0) { throw "bibtex failed for main_report" }
        & xelatex -interaction=nonstopmode -halt-on-error main_report.tex
        if ($LASTEXITCODE -ne 0) { throw "xelatex rerun failed for main_report" }
        & xelatex -interaction=nonstopmode -halt-on-error main_report.tex
        if ($LASTEXITCODE -ne 0) { throw "final xelatex rerun failed for main_report" }
    } finally {
        Pop-Location
    }
}

function Require-Path {
    param([string]$PathValue, [string]$Message)
    if (-not (Test-Path $PathValue)) {
        throw "$Message Missing path: $PathValue"
    }
}

function Stage-Smoke {
    Run-Step "Model tests" @("-m", "pytest", "tests/test_models.py", "tests/test_self_ensemble.py", "-q")
    Run-Step "IDB smoke train" @("-m", "src.train", "src/configs/idb_imdn_x2_smoke.yaml")
    Run-Step "IDB smoke inference" @(
        "-m", "src.infer",
        "--model", "idb_imdn",
        "--scale", "2",
        "--num-features", "16",
        "--num-blocks", "2",
        "--checkpoint", "./checkpoints/idb_imdn_smoke_x2.ckpt",
        "--input", "./data/eval/LR/0821.png",
        "--output", "./results_100pt/idb_imdn_smoke_x2_eval"
    )
    Run-Step "IDB smoke eval" @(
        "-m", "src.eval",
        "--results", "./results_100pt/idb_imdn_smoke_x2_eval",
        "--targets", "./data/eval/HR",
        "--scale", "2",
        "--csv", "./results_100pt/idb_imdn_smoke_x2_eval_metrics.csv"
    )
}

function Stage-SelfEnsemble {
    Require-Path $BestCheckpoint "Self-ensemble learned-model evaluation requires the IMDN 50ep best checkpoint."
    Run-Step "DIV2K self-ensemble" @(
        "tools/run_self_ensemble_eval.py",
        "--dataset-name", "DIV2K",
        "--input", "./data/eval/LR",
        "--target", "./data/eval/HR",
        "--model", "imdn",
        "--scale", "2",
        "--num-features", "32",
        "--num-blocks", "4",
        "--checkpoint", $BestCheckpoint,
        "--output-root", "./results_100pt/self_ensemble"
    )
    $BenchmarkRoot = ".\data\benchmarks"
    foreach ($Name in @("Set5", "Set14", "BSD100", "Urban100")) {
        $LR = Join-Path $BenchmarkRoot "$Name\LR"
        $HR = Join-Path $BenchmarkRoot "$Name\HR"
        if ((Test-Path $LR) -and (Test-Path $HR)) {
            Run-Step "$Name self-ensemble" @(
                "tools/run_self_ensemble_eval.py",
                "--dataset-name", $Name,
                "--input", "./data/benchmarks/$Name/LR",
                "--target", "./data/benchmarks/$Name/HR",
                "--model", "imdn",
                "--scale", "2",
                "--num-features", "32",
                "--num-blocks", "4",
                "--checkpoint", $BestCheckpoint,
                "--output-root", "./results_100pt/self_ensemble"
            )
        } else {
            Write-Host "Skip $Name: benchmark LR/HR directories not found."
        }
    }
}

function Stage-IDB20 {
    Run-Step "IDB-IMDN 20ep train" @("-m", "src.train", "src/configs/idb_imdn_x2_20ep.yaml")
    Run-Step "IDB-IMDN 20ep inference" @(
        "-m", "src.infer",
        "--model", "idb_imdn",
        "--scale", "2",
        "--num-features", "32",
        "--num-blocks", "4",
        "--checkpoint", "./checkpoints/idb_imdn_20ep_x2_best_psnr.ckpt",
        "--input", "./data/eval/LR",
        "--output", "./results_100pt/idb_imdn_20ep_x2_eval"
    )
    Run-Step "IDB-IMDN 20ep eval" @(
        "-m", "src.eval",
        "--results", "./results_100pt/idb_imdn_20ep_x2_eval",
        "--targets", "./data/eval/HR",
        "--scale", "2",
        "--csv", "./results_100pt/idb_imdn_20ep_x2_eval_metrics.csv"
    )
}

function Stage-Assets {
    Run-Step "Summarize 100pt results" @("tools/summarize_100pt_results.py")
    Run-Step "Generate 100pt assets" @("tools/generate_100pt_assets.py")
}

function Stage-Report {
    Run-XeLaTeX
}

function Stage-Package {
    powershell -ExecutionPolicy Bypass -File ".\tools\package_100pt_sprint.ps1"
}

switch ($Stage.ToLower()) {
    "dry-run" { $DryRun = $true; Stage-Smoke; Stage-SelfEnsemble; Stage-IDB20; Stage-Assets; Stage-Report; Stage-Package }
    "smoke" { Stage-Smoke }
    "self-ensemble" { Stage-SelfEnsemble }
    "idb-20" { Stage-IDB20 }
    "assets" { Stage-Assets }
    "report" { Stage-Report }
    "package" { Stage-Package }
    "all" { Stage-Smoke; Stage-SelfEnsemble; Stage-IDB20; Stage-Assets; Stage-Report; Stage-Package }
    default { throw "Unknown Stage: $Stage. Use smoke, self-ensemble, idb-20, assets, report, package, dry-run, or all." }
}
