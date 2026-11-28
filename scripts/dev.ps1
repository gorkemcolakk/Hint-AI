# Docker'sız yerel geliştirme komutları (make yerine). Repo kökünden:
#   powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 <komut>
#
#   setup  venv + Python bağımlılıkları + npm paketleri (ilk kurulumda bir kez)
#   db     PostgreSQL'i başlat + migration'ları uygula
#   seed   demo ebeveyn/çocuk + eşleştirme bağlantısı
#   api    API'yi başlat (http://localhost:8000, /docs)
#   web    Expo web istemcisini başlat (http://localhost:8081)
#   test   API testleri (pytest) + istemci testleri (jest)
#   lint   ruff + mypy + istemci lint/typecheck
#   stop   PostgreSQL'i durdur
param([Parameter(Mandatory = $true)][string]$Command)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Api = Join-Path $Root 'apps\api'
$Client = Join-Path $Root 'apps\client'
$Py = Join-Path $Api '.venv\Scripts\python.exe'
$TestDb = 'postgresql+asyncpg://hint:hint@127.0.0.1:5432/hint_test'

function Invoke-Checked([scriptblock]$Block) {
    & $Block
    if ($LASTEXITCODE -ne 0) { throw "Komut başarısız (çıkış kodu $LASTEXITCODE)" }
}

function Start-Db {
    Push-Location $Api
    try {
        Invoke-Checked { & $Py (Join-Path $Root 'scripts\localdb.py') start }
        Invoke-Checked { & $Py -m alembic upgrade head }
    } finally { Pop-Location }
}

switch ($Command) {
    'setup' {
        Push-Location $Api
        try {
            if (-not (Test-Path $Py)) { Invoke-Checked { uv venv .venv --python 3.13 } }
            Invoke-Checked { uv pip install --python $Py -e '.[dev]' pixeltable-pgserver }
            if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env'; Write-Host '.env oluşturuldu; yerel değerleri kontrol edin.' }
        } finally { Pop-Location }
        Push-Location $Client
        try { Invoke-Checked { npm ci --no-audit --no-fund } } finally { Pop-Location }
    }
    'db' { Start-Db }
    'seed' {
        Start-Db
        Push-Location $Api
        try { Invoke-Checked { & $Py -m scripts.seed_demo } } finally { Pop-Location }
    }
    'api' {
        Start-Db
        Push-Location $Api
        try { & $Py -m uvicorn app.main:app --reload --port 8000 } finally { Pop-Location }
    }
    'web' {
        Push-Location $Client
        try { npm run web } finally { Pop-Location }
    }
    'test' {
        Start-Db
        Push-Location $Api
        try {
            $env:TEST_DATABASE_URL = $TestDb
            Invoke-Checked { & $Py -m pytest -q }
        } finally { Pop-Location }
        Push-Location $Client
        try { Invoke-Checked { npm test -- --ci } } finally { Pop-Location }
    }
    'lint' {
        Push-Location $Api
        try {
            Invoke-Checked { & $Py -m ruff check . }
            Invoke-Checked { & $Py -m ruff format --check . }
            Invoke-Checked { & $Py -m mypy app }
        } finally { Pop-Location }
        Push-Location $Client
        try {
            Invoke-Checked { npm run lint }
            Invoke-Checked { npm run typecheck }
        } finally { Pop-Location }
    }
    'eval' {
        Push-Location $Api
        try {
            Invoke-Checked { & $Py -m evals.run_pii_eval }
            Invoke-Checked { & $Py -m evals.run_safety_eval }
            Invoke-Checked { & $Py -m evals.run_solution_eval }
            Invoke-Checked { & $Py -m evals.run_hint_eval --limit 10 }
        } finally { Pop-Location }
    }
    'stop' { & $Py (Join-Path $Root 'scripts\localdb.py') stop }
    default { throw "Bilinmeyen komut: $Command (setup|db|seed|api|web|test|lint|eval|stop)" }
}
