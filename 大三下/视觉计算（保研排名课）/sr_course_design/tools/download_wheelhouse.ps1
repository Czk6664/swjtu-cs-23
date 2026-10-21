param(
    [string]$PythonExe = "python",
    [string]$WheelDir = ".\vendor\wheels"
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

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$resolvedWheelDir = Join-Path $projectRoot $WheelDir
New-Item -ItemType Directory -Force -Path $resolvedWheelDir | Out-Null

Write-Host "Downloading common dependencies to: $resolvedWheelDir"
Invoke-WithRetry -Description "Downloading common dependency wheels" -Command {
    & $PythonExe -m pip download -r (Join-Path $projectRoot "requirements.txt") -d $resolvedWheelDir --retries 10 --timeout 60
    if ($LASTEXITCODE -ne 0) {
        throw "pip download failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Downloading MindSpore dependency to: $resolvedWheelDir"
Invoke-WithRetry -Description "Downloading MindSpore wheel" -Command {
    & $PythonExe -m pip download mindspore==2.8.0 -d $resolvedWheelDir --retries 10 --timeout 60 -i https://repo.mindspore.cn/pypi/simple --trusted-host repo.mindspore.cn --extra-index-url https://repo.huaweicloud.com/repository/pypi/simple
    if ($LASTEXITCODE -ne 0) {
        throw "MindSpore download failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Wheelhouse is ready."
