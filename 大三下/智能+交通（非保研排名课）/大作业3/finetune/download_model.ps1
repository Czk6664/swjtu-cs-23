# 下载 DeepSeek-R1-Distill-Qwen-7B 原模型到本地 (Windows PowerShell)
#
# 用法:
#   powershell -ExecutionPolicy Bypass -File .\finetune\download_model.ps1
#   powershell -ExecutionPolicy Bypass -File .\finetune\download_model.ps1 -TargetDir "E:\models"
#   powershell -ExecutionPolicy Bypass -File .\finetune\download_model.ps1 -Source huggingface
#
# 行为:
#   1. 检测 python (Anaconda / Python 3.10+ / Microsoft Store 都行)
#   2. 检测 modelscope, 没装就 pip install
#   3. 调 finetune/download_model.py 下载到 <TargetDir>
#   4. 验证两个 safetensors 文件存在并打印总大小

[CmdletBinding()]
param(
    [string]$TargetDir = "D:\models\DeepSeek-R1-Distill-Qwen-7B",
    [ValidateSet("modelscope", "huggingface")]
    [string]$Source = "modelscope",
    [string]$ModelId = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    [string]$HfModelId = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Section($title) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Get-Python {
    $candidates = @("python", "py", "python3")
    foreach ($c in $candidates) {
        $p = Get-Command $c -ErrorAction SilentlyContinue
        if ($p) {
            $v = & $p.Source --version 2>&1
            Write-Host "[env] 找到 Python: $p  ($v)" -ForegroundColor Green
            return $p.Source
        }
    }
    return $null
}

# ---------- 1. 检测 Python ----------------------------------------------------
Write-Section "Step 1/4: 检测 Python 环境"
$python = Get-Python
if (-not $python) {
    Write-Host "[env] 未找到 python" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装任一 Python 3.10+ (推荐):" -ForegroundColor Yellow
    Write-Host "  winget install --id Python.Python.3.12 -e --source winget"
    Write-Host "  或 Anaconda:  https://www.anaconda.com/download"
    Write-Host ""
    exit 1
}

# ---------- 2. 装 modelscope / huggingface_hub ------------------------------
Write-Section "Step 2/4: 准备 Python 包"

$pkg = if ($Source -eq "huggingface") { "huggingface_hub" } else { "modelscope" }
$need = $true
try {
    & $python -c "import $pkg" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $need = $false }
} catch { $need = $true }

if ($need) {
    Write-Host "[pip] 装 $pkg ..." -ForegroundColor Yellow
    & $python -m pip install --upgrade pip 2>&1 | Out-Null
    & $python -m pip install $pkg 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[pip] 安装失败, 请检查网络" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[pip] $pkg 已装" -ForegroundColor Green
}

# ---------- 3. 下载 ----------------------------------------------------------
Write-Section "Step 3/4: 下载模型 (14.2 GB, 约 10-25 分钟)"
Write-Host "[dl] 源:  $Source"
Write-Host "[dl] 模型: $ModelId"
Write-Host "[dl] 目标: $TargetDir"

$target = (Resolve-Path -LiteralPath (Split-Path $TargetDir -Parent) -ErrorAction SilentlyContinue)
if (-not $target) {
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
} elseif (-not (Test-Path -LiteralPath $TargetDir)) {
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
}

if ($Source -eq "huggingface") {
    $env:HF_MODEL_ID  = $HfModelId
    $env:USE_HUGGINGFACE = "1"
    # 走 HF 的 snapshot_download
    & $python -c @"
import os
from huggingface_hub import snapshot_download
mid = os.environ['HF_MODEL_ID']
local = r'$TargetDir'
print(f'[hf] snapshot_download: {mid} -> {local}')
snapshot_download(repo_id=mid, local_dir=local, max_workers=4)
print('[hf] done')
"@
} else {
    $env:MODELSCOPE_MODEL_ID = $ModelId
    $env:MODEL_DIR          = $TargetDir
    & $python "$PSScriptRoot\download_model.py" `
        --model-id $ModelId `
        --local-dir $TargetDir
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "[dl] 下载失败" -ForegroundColor Red
    exit 1
}

# ---------- 4. 验证 ----------------------------------------------------------
Write-Section "Step 4/4: 验证下载"
if (-not (Test-Path -LiteralPath $TargetDir)) {
    Write-Host "[verify] 目录不存在: $TargetDir" -ForegroundColor Red
    exit 1
}

$files = Get-ChildItem -LiteralPath $TargetDir -Recurse -File
$totalMB = [math]::Round(($files | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host "[verify] 文件数: $($files.Count)"
Write-Host "[verify] 总大小: $totalMB MB"

$safetensors = Get-ChildItem -LiteralPath $TargetDir -Filter "*.safetensors" -Recurse
foreach ($f in $safetensors) {
    $sizeGB = [math]::Round($f.Length / 1GB, 2)
    Write-Host ("  - {0}  ({1} GB)" -f $f.Name, $sizeGB)
}

if ($safetensors.Count -lt 2) {
    Write-Host "[verify] 警告: 期望至少 2 个 safetensors 文件, 实际找到 $($safetensors.Count)" -ForegroundColor Yellow
    Write-Host "[verify] 可能是下载未完成, 可重跑脚本 (ModelScope/HF 会断点续传)" -ForegroundColor Yellow
} else {
    Write-Host "[verify] OK - 模型已就绪: $TargetDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "下一步: 把 LoRA 适配器目录 (含 adapter_model.safetensors) 也复制到这台机器, 然后合并 -> 量化 -> Ollama" -ForegroundColor Cyan
