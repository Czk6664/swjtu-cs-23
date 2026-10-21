param(
    [string]$OutputRoot = "dist"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$outputRootPath = Join-Path $projectRoot $OutputRoot
$stagingDir = Join-Path $outputRootPath "tt100k_rtx4070_portable"
$zipPath = Join-Path $outputRootPath "tt100k_rtx4070_portable.zip"

if (Test-Path $stagingDir) {
    Remove-Item -LiteralPath $stagingDir -Recurse -Force
}

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Path $stagingDir | Out-Null

$itemsToCopy = @(
    "README.md",
    "README_4070_AUTOTUNE.md",
    "requirements.txt",
    "train.py",
    "val.py",
    "predict.py",
    "export_report_assets.py",
    "configs\experiments",
    "scripts\autotune_rtx4070.py",
    "scripts\prepare_tt100k.py",
    "scripts\split_tt100k.py",
    "scripts\collect_metrics.py",
    "src"
)

foreach ($relativePath in $itemsToCopy) {
    $sourcePath = Join-Path $projectRoot $relativePath
    if (-not (Test-Path $sourcePath)) {
        Write-Warning "Skip missing path: $relativePath"
        continue
    }

    $destinationPath = Join-Path $stagingDir $relativePath
    $destinationParent = Split-Path -Parent $destinationPath
    if ($destinationParent -and -not (Test-Path $destinationParent)) {
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
    }

    Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Recurse -Force
}

Get-ChildItem -LiteralPath $stagingDir -Directory -Recurse -Force |
    Where-Object { $_.Name -eq "__pycache__" } |
    Remove-Item -Recurse -Force

Get-ChildItem -LiteralPath $stagingDir -File -Recurse -Force |
    Where-Object { $_.Extension -eq ".pyc" } |
    Remove-Item -Force

Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -Force

Write-Host "Created package:"
Write-Host $zipPath
