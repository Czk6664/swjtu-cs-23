param(
    [string]$EnvName = "sr-course-design",
    [switch]$RunEdge50,
    [switch]$SkipTests,
    [switch]$SummarizeOnly,
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

function Backup-Path {
    param([string]$Path)

    if (Test-Path $Path) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backup = "$Path.bak_$timestamp"
        Move-Item -LiteralPath $Path -Destination $backup -Force
        Write-Host "Existing output moved to: $backup"
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
        [string]$TrainLog,
        [string]$OutputDir,
        [string]$MetricCsv
    )

    Backup-Path $Checkpoint
    Backup-Path $TrainLog
    Backup-Path $OutputDir
    Backup-Path $MetricCsv

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

function Read-MetricAverage {
    param(
        [string]$Label,
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return $null
    }

    $rows = Import-Csv $Path
    if ($rows.Count -eq 0) {
        return $null
    }

    $psnr = ($rows | ForEach-Object { [double]$_.psnr } | Measure-Object -Average).Average
    $ssim = ($rows | ForEach-Object { [double]$_.ssim } | Measure-Object -Average).Average
    [PSCustomObject]@{
        Method = $Label
        Count = $rows.Count
        PSNR = [math]::Round($psnr, 4)
        SSIM = [math]::Round($ssim, 4)
        Csv = $Path
    }
}

function Write-Summary {
    $summaryDir = Join-Path $ProjectRoot "results"
    New-Item -ItemType Directory -Force -Path $summaryDir | Out-Null

    $items = @(
        @{ Label = "Bicubic"; Path = "./results/bicubic_x2_eval_metrics.csv" },
        @{ Label = "SRCNN 5ep"; Path = "./results/srcnn_x2_eval_metrics.csv" },
        @{ Label = "IMDN edge 5ep"; Path = "./results/imdn_x2_eval_metrics.csv" },
        @{ Label = "IMDN no-edge 5ep"; Path = "./results/imdn_x2_no_edge_eval_metrics.csv" },
        @{ Label = "IMDN no-edge 20ep"; Path = "./results/imdn_x2_no_edge_20ep_eval_metrics.csv" },
        @{ Label = "IMDN edge 0.01 20ep"; Path = "./results/imdn_edge_w001_20ep_x2_eval_metrics.csv" },
        @{ Label = "IMDN no-edge 50ep"; Path = "./results/imdn_x2_no_edge_50ep_eval_metrics.csv" },
        @{ Label = "IMDN edge 0.01 50ep"; Path = "./results/imdn_edge_w001_50ep_x2_eval_metrics.csv" }
    )

    $rows = foreach ($item in $items) {
        Read-MetricAverage -Label $item.Label -Path $item.Path
    }

    $rows = @($rows | Where-Object { $_ -ne $null })
    $csvPath = Join-Path $summaryDir "long_training_summary.csv"
    $mdPath = Join-Path $summaryDir "long_training_summary.md"
    $rows | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8

    $lines = @()
    $lines += "# Long Training Summary"
    $lines += ""
    $lines += "| Method | Count | PSNR | SSIM |"
    $lines += "|---|---:|---:|---:|"
    foreach ($row in $rows) {
        $lines += "| $($row.Method) | $($row.Count) | $($row.PSNR) | $($row.SSIM) |"
    }
    $lines += ""
    $lines += "Generated at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $lines | Set-Content -Path $mdPath -Encoding UTF8

    Write-Host ""
    Write-Host "Summary written:"
    Write-Host "  $csvPath"
    Write-Host "  $mdPath"
    $rows | Format-Table -AutoSize
}

Set-Location $ProjectRoot

Assert-File "./src/configs/imdn_x2_no_edge_50ep.yaml"
Assert-File "./src/configs/imdn_x2_edge_w001_50ep.yaml"

if (-not $SkipTests -and -not $SummarizeOnly) {
    Invoke-Step "Smoke tests" {
        Invoke-Python -m src.smoke_test_ms
        Invoke-Python -m pytest tests/test_losses.py tests/test_models.py tests/test_dataset.py tests/test_infer_smoke.py tests/test_metrics.py -q
    }
}

if (-not $SummarizeOnly) {
    Run-TrainInferEval `
        -Name "IMDN no-edge 50 epoch" `
        -Config "./src/configs/imdn_x2_no_edge_50ep.yaml" `
        -Checkpoint "./checkpoints/imdn_no_edge_50ep_x2.ckpt" `
        -TrainLog "./logs/imdn_x2_no_edge_50ep_metrics.csv" `
        -OutputDir "./results/imdn_x2_no_edge_50ep_eval" `
        -MetricCsv "./results/imdn_x2_no_edge_50ep_eval_metrics.csv"

    if ($RunEdge50) {
        Run-TrainInferEval `
            -Name "IMDN edge 0.01 50 epoch" `
            -Config "./src/configs/imdn_x2_edge_w001_50ep.yaml" `
            -Checkpoint "./checkpoints/imdn_edge_w001_50ep_x2.ckpt" `
            -TrainLog "./logs/imdn_x2_edge_w001_50ep_metrics.csv" `
            -OutputDir "./results/imdn_edge_w001_50ep_x2_eval" `
            -MetricCsv "./results/imdn_edge_w001_50ep_x2_eval_metrics.csv"
    }
}

Invoke-Step "Write metric summary" {
    Write-Summary
}

if ($RegenerateFigures) {
    Invoke-Step "Regenerate report figures" {
        Invoke-Python tools/generate_report_assets.py
    }
}

Write-Host ""
Write-Host "Next experiments workflow completed."
Write-Host "Recommended file to send back:"
Write-Host "  results/long_training_summary.md"
