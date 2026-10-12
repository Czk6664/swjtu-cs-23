param(
    [string]$EnvName = "sr-course-design",
    [switch]$Run50Epoch,
    [switch]$SkipTests,
    [switch]$RegenerateFigures
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

function Assert-File {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Required file does not exist: $Path"
    }
}

function Assert-ImageCount {
    param(
        [string]$Directory,
        [int]$Expected = 100
    )

    $count = (Get-ChildItem -Path $Directory -Filter *.png -File -ErrorAction SilentlyContinue | Measure-Object).Count
    if ($count -ne $Expected) {
        throw "Expected $Expected PNG files in $Directory, found $count"
    }
}

function Assert-CsvRows {
    param(
        [string]$Path,
        [int]$Expected = 100
    )

    Assert-File $Path
    $rows = Import-Csv $Path
    if ($rows.Count -ne $Expected) {
        throw "Expected $Expected rows in $Path, found $($rows.Count)"
    }
}

function Run-TrainInferEval {
    param(
        [string]$Name,
        [string]$Config,
        [string]$Checkpoint,
        [string]$OutputDir,
        [string]$MetricCsv
    )

    Invoke-Step "Training: $Name" {
        Invoke-Python -m src.train $Config
    }

    Assert-File $Checkpoint

    Invoke-Step "Inference: $Name" {
        Invoke-Python -m src.infer --model imdn --scale 2 --num-features 32 --checkpoint $Checkpoint --input ./data/eval/LR --output $OutputDir
    }

    Assert-ImageCount $OutputDir 100

    Invoke-Step "Evaluation: $Name" {
        Invoke-Python -m src.eval --results $OutputDir --targets ./data/eval/HR --scale 2 --csv $MetricCsv
    }

    Assert-CsvRows $MetricCsv 100
}

Set-Location $ProjectRoot

Assert-File "./src/configs/imdn_x2_no_edge_20ep.yaml"
Assert-File "./src/configs/imdn_x2_edge_w001_20ep.yaml"
Assert-File "./src/configs/imdn_x2_no_edge_50ep.yaml"

if (-not $SkipTests) {
    Invoke-Step "Smoke tests" {
        Invoke-Python -m src.smoke_test_ms
        Invoke-Python -m pytest tests/test_losses.py tests/test_models.py tests/test_dataset.py tests/test_infer_smoke.py tests/test_metrics.py -q
    }
}

Run-TrainInferEval `
    -Name "IMDN no-edge 20 epoch" `
    -Config "./src/configs/imdn_x2_no_edge_20ep.yaml" `
    -Checkpoint "./checkpoints/imdn_no_edge_20ep_x2.ckpt" `
    -OutputDir "./results/imdn_x2_no_edge_20ep_eval" `
    -MetricCsv "./results/imdn_x2_no_edge_20ep_eval_metrics.csv"

Run-TrainInferEval `
    -Name "IMDN edge 0.01 20 epoch" `
    -Config "./src/configs/imdn_x2_edge_w001_20ep.yaml" `
    -Checkpoint "./checkpoints/imdn_edge_w001_20ep_x2.ckpt" `
    -OutputDir "./results/imdn_edge_w001_20ep_x2_eval" `
    -MetricCsv "./results/imdn_edge_w001_20ep_x2_eval_metrics.csv"

if ($Run50Epoch) {
    Run-TrainInferEval `
        -Name "IMDN no-edge 50 epoch" `
        -Config "./src/configs/imdn_x2_no_edge_50ep.yaml" `
        -Checkpoint "./checkpoints/imdn_no_edge_50ep_x2.ckpt" `
        -OutputDir "./results/imdn_x2_no_edge_50ep_eval" `
        -MetricCsv "./results/imdn_x2_no_edge_50ep_eval_metrics.csv"
}

if ($RegenerateFigures) {
    Invoke-Step "Regenerate report figures" {
        Invoke-Python tools/generate_report_assets.py
    }
}

Write-Host ""
Write-Host "Long training workflow completed."
Write-Host "Key outputs:"
Write-Host "  checkpoints/imdn_no_edge_20ep_x2.ckpt"
Write-Host "  checkpoints/imdn_edge_w001_20ep_x2.ckpt"
Write-Host "  results/imdn_x2_no_edge_20ep_eval_metrics.csv"
Write-Host "  results/imdn_edge_w001_20ep_x2_eval_metrics.csv"
if ($Run50Epoch) {
    Write-Host "  checkpoints/imdn_no_edge_50ep_x2.ckpt"
    Write-Host "  results/imdn_x2_no_edge_50ep_eval_metrics.csv"
}
