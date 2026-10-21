param(
    [string]$OutputDir = ".\dist",
    [string]$PackageName = "sr_course_design_portable",
    [switch]$IncludePredictedImages,
    [switch]$NoZip
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$resolvedOutputDir = Join-Path $projectRoot $OutputDir
$stagingDir = Join-Path $resolvedOutputDir $PackageName
$zipPath = Join-Path $resolvedOutputDir "$PackageName.zip"

function Copy-Directory {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (-not (Test-Path $Source)) {
        return
    }

    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    robocopy $Source $Destination /E /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed: $Source -> $Destination"
    }
}

function Copy-FileIfExists {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (Test-Path $Source) {
        New-Item -ItemType Directory -Force -Path (Split-Path $Destination -Parent) | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
    }
}

if (Test-Path $stagingDir) {
    Remove-Item -LiteralPath $stagingDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $stagingDir | Out-Null

Write-Host "Project root: $projectRoot"
Write-Host "Staging package: $stagingDir"

$rootFiles = @(
    "README.md",
    "PACKAGED_USAGE.md",
    "requirements.txt",
    "requirements-full.txt",
    "environment.yml",
    "setup_windows.ps1",
    "run_smoke_windows.ps1",
    "run_all_windows.ps1",
    "literature_review.md",
    "project_plan.md",
    "report_outline.md"
)

foreach ($file in $rootFiles) {
    Copy-FileIfExists (Join-Path $projectRoot $file) (Join-Path $stagingDir $file)
}

foreach ($dir in @("src", "tests", "tools", "checkpoints", "logs")) {
    Copy-Directory (Join-Path $projectRoot $dir) (Join-Path $stagingDir $dir)
}

Copy-Directory (Join-Path $projectRoot "vendor") (Join-Path $stagingDir "vendor")

Copy-Directory (Join-Path $projectRoot "report") (Join-Path $stagingDir "report")

foreach ($dataDir in @("LR", "HR", "eval")) {
    Copy-Directory (Join-Path $projectRoot "data\$dataDir") (Join-Path $stagingDir "data\$dataDir")
}

New-Item -ItemType Directory -Force -Path (Join-Path $stagingDir "results") | Out-Null
Get-ChildItem -Path (Join-Path $projectRoot "results") -File -ErrorAction SilentlyContinue |
    ForEach-Object {
        Copy-FileIfExists $_.FullName (Join-Path $stagingDir "results\$($_.Name)")
    }

if ($IncludePredictedImages) {
    Get-ChildItem -Path (Join-Path $projectRoot "results") -Directory -ErrorAction SilentlyContinue |
        ForEach-Object {
            Copy-Directory $_.FullName (Join-Path $stagingDir "results\$($_.Name)")
        }
}

$manifestPath = Join-Path $stagingDir "PACKAGE_MANIFEST.txt"
$manifest = @()
$manifest += "Package: $PackageName"
$manifest += "Created: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
$manifest += "Source: $projectRoot"
$manifest += "Includes predicted images: $IncludePredictedImages"
$manifest += ""
$manifest += "Included top-level items:"
Get-ChildItem -Force $stagingDir | Sort-Object Name | ForEach-Object {
    $manifest += "- $($_.Name)"
}
$manifest | Set-Content -Encoding UTF8 $manifestPath

$totalBytes = (Get-ChildItem -Recurse -File $stagingDir | Measure-Object -Property Length -Sum).Sum
Write-Host ("Staging size: {0:N2} GB" -f ($totalBytes / 1GB))

if (-not $NoZip) {
    if (Test-Path $zipPath) {
        Remove-Item -LiteralPath $zipPath -Force
    }

    $sevenZip = Get-Command 7z -ErrorAction SilentlyContinue
    if ($sevenZip) {
        Write-Host "Creating zip with 7-Zip: $zipPath"
        Push-Location $stagingDir
        try {
            & $sevenZip.Source a -tzip $zipPath ".\*" -mx=5
            if ($LASTEXITCODE -ne 0) {
                throw "7-Zip failed with exit code $LASTEXITCODE"
            }
        }
        finally {
            Pop-Location
        }
    }
    else {
        $tar = Get-Command tar -ErrorAction SilentlyContinue
        if ($tar) {
            Write-Host "Creating zip with tar.exe: $zipPath"
            & $tar.Source -a -cf $zipPath -C $stagingDir .
            if ($LASTEXITCODE -ne 0) {
                throw "tar.exe failed with exit code $LASTEXITCODE"
            }
        }
        else {
            Write-Host "Creating zip with Compress-Archive: $zipPath"
            Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -CompressionLevel Optimal
        }
    }

    $zipInfo = Get-Item $zipPath
    Write-Host ("Zip size: {0:N2} GB" -f ($zipInfo.Length / 1GB))
}

Write-Host "Done."
