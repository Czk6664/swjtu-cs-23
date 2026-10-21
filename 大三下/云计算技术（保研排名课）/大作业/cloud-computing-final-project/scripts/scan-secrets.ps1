$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$patterns = @(
    "AKIA[0-9A-Z]{16}",
    "SK[A-Za-z0-9/_+=-]{20,}",
    "AccessKeyId",
    "SecretAccessKey",
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY"
)

$hits = @()
foreach ($pattern in $patterns) {
    $found = Get-ChildItem -Path $root -Recurse -File |
        Where-Object { $_.FullName -notmatch "\\.git\\" -and $_.Name -ne "scan-secrets.ps1" } |
        Select-String -Pattern $pattern -ErrorAction SilentlyContinue
    if ($found) {
        $hits += $found
    }
}

if ($hits.Count -gt 0) {
    $hits | ForEach-Object { Write-Host "$($_.Path):$($_.LineNumber) $($_.Line)" -ForegroundColor Red }
    exit 1
}

Write-Host "No obvious credential patterns found." -ForegroundColor Green
