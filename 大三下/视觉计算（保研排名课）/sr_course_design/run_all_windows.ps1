param(
    [string]$EnvName = "sr-course-design",
    [switch]$SkipSetup,
    [ValidateSet("none", "quick", "main")]
    [string]$TrainMode = "none",
    [switch]$CompileReport
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "========== $Name =========="
    & $Command
}

function Invoke-Python {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    conda run -n $EnvName python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: python $($Arguments -join ' ')"
    }
}

Set-Location $ProjectRoot

if (-not $SkipSetup) {
    Invoke-Step "Install or update environment" {
        powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "setup_windows.ps1") -EnvName $EnvName
    }
}

Invoke-Step "Smoke tests" {
    Invoke-Python -m src.smoke_test_ms
    Invoke-Python -m pytest tests/test_losses.py tests/test_models.py tests/test_dataset.py tests/test_infer_smoke.py tests/test_metrics.py -q
}

if ($TrainMode -eq "quick") {
    Invoke-Step "Quick training: SRCNN fair" {
        Invoke-Python -m src.train src/configs/srcnn_x2_fair_quick.yaml
    }
    Invoke-Step "Quick training: IMDN no-edge" {
        Invoke-Python -m src.train src/configs/imdn_x2_no_edge_fair_quick.yaml
    }
    Invoke-Step "Quick training: IMDN edge 0.01" {
        Invoke-Python -m src.train src/configs/imdn_x2_edge_w001_quick.yaml
    }
    Invoke-Step "Quick training: IMDN edge 0.02" {
        Invoke-Python -m src.train src/configs/imdn_x2_edge_w002_quick.yaml
    }
    Invoke-Step "Quick training: IMDN Laplacian" {
        Invoke-Python -m src.train src/configs/imdn_x2_laplacian_quick.yaml
    }
}
elseif ($TrainMode -eq "main") {
    Invoke-Step "Main training: SRCNN" {
        Invoke-Python -m src.train src/configs/srcnn_x2.yaml
    }
    Invoke-Step "Main training: IMDN edge" {
        Invoke-Python -m src.train src/configs/imdn_x2.yaml
    }
    Invoke-Step "Main training: IMDN no-edge" {
        Invoke-Python -m src.train src/configs/imdn_x2_no_edge.yaml
    }
}

$inferenceJobs = @(
    @{
        Name = "Bicubic"
        InferArgs = @("-m", "src.infer", "--model", "bicubic", "--scale", "2", "--input", "./data/eval/LR", "--output", "./results/bicubic_x2_eval")
        EvalArgs = @("-m", "src.eval", "--results", "./results/bicubic_x2_eval", "--targets", "./data/eval/HR", "--scale", "2", "--csv", "./results/bicubic_x2_eval_metrics.csv")
    },
    @{
        Name = "SRCNN"
        InferArgs = @("-m", "src.infer", "--model", "srcnn", "--scale", "2", "--checkpoint", "./checkpoints/srcnn_x2.ckpt", "--input", "./data/eval/LR", "--output", "./results/srcnn_x2_eval")
        EvalArgs = @("-m", "src.eval", "--results", "./results/srcnn_x2_eval", "--targets", "./data/eval/HR", "--scale", "2", "--csv", "./results/srcnn_x2_eval_metrics.csv")
    },
    @{
        Name = "IMDN edge"
        InferArgs = @("-m", "src.infer", "--model", "imdn", "--scale", "2", "--num-features", "32", "--checkpoint", "./checkpoints/imdn_x2.ckpt", "--input", "./data/eval/LR", "--output", "./results/imdn_x2_eval")
        EvalArgs = @("-m", "src.eval", "--results", "./results/imdn_x2_eval", "--targets", "./data/eval/HR", "--scale", "2", "--csv", "./results/imdn_x2_eval_metrics.csv")
    },
    @{
        Name = "IMDN no-edge"
        InferArgs = @("-m", "src.infer", "--model", "imdn", "--scale", "2", "--num-features", "32", "--checkpoint", "./checkpoints/imdn_no_edge_x2.ckpt", "--input", "./data/eval/LR", "--output", "./results/imdn_x2_no_edge_eval")
        EvalArgs = @("-m", "src.eval", "--results", "./results/imdn_x2_no_edge_eval", "--targets", "./data/eval/HR", "--scale", "2", "--csv", "./results/imdn_x2_no_edge_eval_metrics.csv")
    },
    @{
        Name = "IMDN Laplacian quick"
        InferArgs = @("-m", "src.infer", "--model", "imdn", "--scale", "2", "--num-features", "32", "--checkpoint", "./checkpoints/imdn_laplacian_quick_x2.ckpt", "--input", "./data/eval/LR", "--output", "./results/imdn_laplacian_quick_x2_eval")
        EvalArgs = @("-m", "src.eval", "--results", "./results/imdn_laplacian_quick_x2_eval", "--targets", "./data/eval/HR", "--scale", "2", "--csv", "./results/imdn_laplacian_quick_x2_eval_metrics.csv")
    }
)

foreach ($job in $inferenceJobs) {
    Invoke-Step "Inference: $($job.Name)" {
        Invoke-Python -Arguments $job.InferArgs
    }
    Invoke-Step "Evaluation: $($job.Name)" {
        Invoke-Python -Arguments $job.EvalArgs
    }
}

Invoke-Step "Regenerate report figures" {
    Invoke-Python tools/generate_report_assets.py
}

if ($CompileReport) {
    Invoke-Step "Compile LaTeX report" {
        $xelatex = Get-Command xelatex -ErrorAction SilentlyContinue
        $bibtex = Get-Command bibtex -ErrorAction SilentlyContinue
        if (-not $xelatex -or -not $bibtex) {
            throw "xelatex/bibtex not found. Install TeX Live first, or run without -CompileReport."
        }
        Push-Location (Join-Path $ProjectRoot "report")
        try {
            xelatex -interaction=nonstopmode -halt-on-error main_report.tex
            bibtex main_report
            xelatex -interaction=nonstopmode -halt-on-error main_report.tex
            xelatex -interaction=nonstopmode -halt-on-error main_report.tex
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "All requested steps completed."
Write-Host "Report PDF: $ProjectRoot\report\main_report.pdf"
Write-Host "Metrics CSV: $ProjectRoot\results"
