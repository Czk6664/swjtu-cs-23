param(
    [string]$EnvName = "sr-course-design"
)

$ErrorActionPreference = "Stop"

function Invoke-WithRetry {
    param(
        [scriptblock]$Command,
        [string]$Description,
        [int]$MaxAttempts = 5,
        [int]$DelaySeconds = 10
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            Write-Host "[$attempt/$MaxAttempts] $Description"
            & $Command
            return
        }
        catch {
            if ($attempt -eq $MaxAttempts) {
                throw
            }
            Write-Warning "$Description failed: $($_.Exception.Message)"
            Write-Host "Retrying in $DelaySeconds seconds..."
            Start-Sleep -Seconds $DelaySeconds
        }
    }
}

function Find-Conda {
    $conda = Get-Command conda -ErrorAction SilentlyContinue
    if ($conda) {
        return $conda.Source
    }

    $candidates = @(
        "$env:USERPROFILE\anaconda3\Scripts\conda.exe",
        "$env:USERPROFILE\miniconda3\Scripts\conda.exe",
        "D:\Anaconda\Scripts\conda.exe",
        "D:\Miniconda3\Scripts\conda.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Conda was not found. Install Anaconda or Miniconda, then rerun this script."
}

$condaExe = Find-Conda

Write-Host "Using conda: $condaExe"
Write-Host "Creating or updating environment: $EnvName"

$existingEnv = & $condaExe env list | Select-String -Pattern "^\s*$([regex]::Escape($EnvName))\s+"
if (-not $existingEnv) {
    Invoke-WithRetry -Description "Creating conda environment" -Command {
        & $condaExe create -y -n $EnvName python=3.11 pip
        if ($LASTEXITCODE -ne 0) {
            throw "conda create failed with exit code $LASTEXITCODE"
        }
    }
}
else {
    Write-Host "Environment already exists: $EnvName"
}

Invoke-WithRetry -Description "Upgrading pip" -Command {
    & $condaExe run -n $EnvName python -m pip install --upgrade pip --retries 10 --timeout 60
    if ($LASTEXITCODE -ne 0) {
        throw "pip upgrade failed with exit code $LASTEXITCODE"
    }
}

$wheelDir = Join-Path $PSScriptRoot "vendor\wheels"
if (Test-Path $wheelDir) {
    Write-Host "Installing dependencies from local wheelhouse: $wheelDir"
    Invoke-WithRetry -Description "Installing project dependencies from local wheelhouse" -Command {
        & $condaExe run -n $EnvName python -m pip install --no-index --find-links $wheelDir -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "local dependency install failed with exit code $LASTEXITCODE"
        }
    }
    Invoke-WithRetry -Description "Installing MindSpore from local wheelhouse" -Command {
        & $condaExe run -n $EnvName python -m pip install --no-index --find-links $wheelDir mindspore==2.8.0
        if ($LASTEXITCODE -ne 0) {
            throw "local MindSpore install failed with exit code $LASTEXITCODE"
        }
    }
}
else {
    Write-Host "Local wheelhouse not found; installing dependencies from online indexes."
    Invoke-WithRetry -Description "Installing project dependencies from online indexes" -Command {
        & $condaExe run -n $EnvName python -m pip install -r requirements.txt --retries 10 --timeout 60
        if ($LASTEXITCODE -ne 0) {
            throw "online dependency install failed with exit code $LASTEXITCODE"
        }
    }
    Invoke-WithRetry -Description "Installing MindSpore from online indexes" -Command {
        & $condaExe run -n $EnvName python -m pip install mindspore==2.8.0 --retries 10 --timeout 60 -i https://repo.mindspore.cn/pypi/simple --trusted-host repo.mindspore.cn --extra-index-url https://repo.huaweicloud.com/repository/pypi/simple
        if ($LASTEXITCODE -ne 0) {
            throw "online MindSpore install failed with exit code $LASTEXITCODE"
        }
    }
}

Write-Host ""
Write-Host "Environment is ready."
Write-Host "Run smoke test:"
Write-Host "  conda run -n $EnvName python -m src.smoke_test_ms"
Write-Host ""
Write-Host "Run bicubic inference example:"
Write-Host "  conda run -n $EnvName python -m src.infer --model bicubic --scale 2 --input ./data/eval/LR --output ./results/bicubic_x2_eval"
