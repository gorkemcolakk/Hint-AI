# Hint.ai

7–17 yaş öğrenciler için cevabı değil, kademeli ipucu veren AI öğrenme arkadaşı.

## Durum: M0 — Altyapı iskeleti

- Monorepo iskeleti, Docker Compose (api, db, redis), CI, lint, `healthz`, ortam değişkeni şablonu.
- Kabul kriteri: `docker compose up` ile çalışır; CI yeşil.

## Hızlı başlangıç (Docker)

```powershell
docker compose up --build
```

```powershell
curl http://localhost:8000/healthz   # {"status":"ok",...}
curl http://localhost:8000/readyz    # db+redis hazırsa 200, değilse 503
```

## Yerel geliştirme (Docker'sız)

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
mypy app
uvicorn app.main:app --reload
```

## Komutlar (Linux/macOS/CI)

- `make up` / `make down`
- `make test` / `make lint`

Detaylı plan: [docs/master-plan.md](docs/master-plan.md)
