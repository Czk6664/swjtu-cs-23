$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root "backend"

Push-Location $backend
try {
    $env:PYTHONPATH = $backend
    if (-not $env:REDIS_HOST) { $env:REDIS_HOST = "localhost" }
    if (-not $env:REDIS_PORT) { $env:REDIS_PORT = "6379" }
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    @'
from app import app

client = app.test_client()
response = client.get("/api/ping")
print(response.status_code, response.get_json())
assert response.status_code == 200
assert response.get_json()["status"] == "ok"
'@ | python -
}
finally {
    Pop-Location
}
