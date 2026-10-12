param(
    [string]$Python = "python",
    [switch]$DryRun,
    [switch]$SkipTraining,
    [switch]$SkipReport,
    [string]$Stage = "all"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
if ((Split-Path -Leaf $Root) -eq "scripts") {
    $Root = Split-Path -Parent $Root
}
Set-Location $Root

function Invoke-Step {
    param([string]$Label, [string[]]$Command)
    Write-Host ""
    Write-Host "========== $Label =========="
    Write-Host ($Command -join " ")
    if (-not $DryRun) {
        & $Command[0] @($Command[1..($Command.Length - 1)])
        if ($LASTEXITCODE -ne 0) {
            throw "Step failed: $Label"
        }
    }
}

$Jobs = @(
    @{Name="srcnn_20ep"; Config="src/configs/srcnn_x2_20ep.yaml"; InferModel="srcnn"; Features="32"; Blocks="4"},
    @{Name="imdn_width16_20ep"; Config="src/configs/imdn_x2_width16_20ep.yaml"; InferModel="imdn"; Features="16"; Blocks="4"},
    @{Name="imdn_width48_20ep"; Config="src/configs/imdn_x2_width48_20ep.yaml"; InferModel="imdn"; Features="48"; Blocks="4"},
    @{Name="imdn_depth2_20ep"; Config="src/configs/imdn_x2_depth2_20ep.yaml"; InferModel="imdn"; Features="32"; Blocks="2"},
    @{Name="imdn_depth6_20ep"; Config="src/configs/imdn_x2_depth6_20ep.yaml"; InferModel="imdn"; Features="32"; Blocks="6"},
    @{Name="imdn_no_edge_20ep_step_lr"; Config="src/configs/imdn_x2_no_edge_20ep_step_lr.yaml"; InferModel="imdn"; Features="32"; Blocks="4"},
    @{Name="imdn_no_edge_20ep_cosine_lr"; Config="src/configs/imdn_x2_no_edge_20ep_cosine_lr.yaml"; InferModel="imdn"; Features="32"; Blocks="4"},
    @{Name="ca_imdn_no_edge_20ep"; Config="src/configs/ca_imdn_x2_no_edge_20ep.yaml"; InferModel="ca_imdn"; Features="32"; Blocks="4"},
    @{Name="ca_imdn_no_edge_50ep"; Config="src/configs/ca_imdn_x2_no_edge_50ep.yaml"; InferModel="ca_imdn"; Features="32"; Blocks="4"},
    @{Name="ca_imdn_edge_w001_20ep"; Config="src/configs/ca_imdn_x2_edge_w001_20ep.yaml"; InferModel="ca_imdn"; Features="32"; Blocks="4"},
    @{Name="ca_imdn_no_edge_20ep_cosine_lr"; Config="src/configs/ca_imdn_x2_no_edge_20ep_cosine_lr.yaml"; InferModel="ca_imdn"; Features="32"; Blocks="4"}
)

$EvalInput = "./data/eval/LR"
if ($Stage -eq "smoke") {
    $Jobs = @(
        @{Name="ca_imdn_smoke"; Config="src/configs/ca_imdn_x2_smoke.yaml"; InferModel="ca_imdn"; Features="16"; Blocks="2"}
    )
    $EvalInput = "./data/eval/LR/0821.png"
}

foreach ($Job in $Jobs) {
    $Checkpoint = "checkpoints/$($Job.Name)_x2.ckpt"
    $Output = "results/$($Job.Name)_x2_eval"
    $Metrics = "results/$($Job.Name)_x2_eval_metrics.csv"
    if (-not $SkipTraining) {
        Invoke-Step "Train $($Job.Name)" @($Python, "-m", "src.train", $Job.Config)
    }
    if ((Test-Path $Output) -and (-not $DryRun)) {
        Remove-Item -LiteralPath $Output -Recurse -Force
    }
    Invoke-Step "Infer $($Job.Name)" @(
        $Python, "-m", "src.infer",
        "--model", $Job.InferModel,
        "--scale", "2",
        "--num-features", $Job.Features,
        "--num-blocks", $Job.Blocks,
        "--checkpoint", $Checkpoint,
        "--input", $EvalInput,
        "--output", $Output
    )
    Invoke-Step "Evaluate $($Job.Name)" @(
        $Python, "-m", "src.eval",
        "--results", $Output,
        "--targets", "./data/eval/HR",
        "--scale", "2",
        "--csv", $Metrics
    )
}

Invoke-Step "Count parameters" @($Python, "tools/count_parameters.py")
Invoke-Step "Summarize experiments" @($Python, "tools/summarize_experiments.py")

if (Test-Path "results/ca_imdn_no_edge_50ep_x2_eval/0821.png") {
    Invoke-Step "Frequency analysis" @($Python, "tools/analyze_frequency.py", "--filename", "0821.png")
}

foreach ($Benchmark in @("Set5", "Set14", "BSD100", "Urban100")) {
    $BenchmarkRoot = "data/benchmarks/$Benchmark"
    if (Test-Path "$BenchmarkRoot/LR") {
        Invoke-Step "Benchmark Bicubic $Benchmark" @($Python, "tools/run_benchmark_eval.py", "--benchmark-root", $BenchmarkRoot, "--name", $Benchmark, "--model", "bicubic", "--scale", "2")
        if (Test-Path "checkpoints/ca_imdn_no_edge_50ep_x2.ckpt") {
            Invoke-Step "Benchmark CA-IMDN $Benchmark" @($Python, "tools/run_benchmark_eval.py", "--benchmark-root", $BenchmarkRoot, "--name", $Benchmark, "--model", "ca_imdn", "--scale", "2", "--checkpoint", "checkpoints/ca_imdn_no_edge_50ep_x2.ckpt")
        }
    }
}

if (-not $SkipReport) {
    Invoke-Step "Regenerate report assets" @($Python, "tools/generate_report_assets.py")
    if (Get-Command xelatex -ErrorAction SilentlyContinue) {
        Push-Location report
        try {
            Invoke-Step "Compile report pass 1" @("xelatex", "-interaction=nonstopmode", "-halt-on-error", "main_report.tex")
            Invoke-Step "Compile report pass 2" @("xelatex", "-interaction=nonstopmode", "-halt-on-error", "main_report.tex")
        } finally {
            Pop-Location
        }
    }
}

Write-Host ""
Write-Host "All requested CA-IMDN experiment steps completed."
