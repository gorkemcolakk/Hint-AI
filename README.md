# Hint.ai 🎓

> Cevabı değil, kademeli ipucu veren AI öğrenme arkadaşı — 7–17 yaş.

![CI](https://github.com/gorkemcolakk/Hint-AI/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)

Hint.ai, öğrencinin takıldığı yeri tespit edip **cevabı söylemeden**, adım adım ipucu vererek kendi başına çözmesini sağlar. Ebeveyn paneli ve öğretmen paneliyle birlikte gelir.

## Yol haritası

| Milestone | İçerik | Durum |
|---|---|---|
| **M0** | Altyapı iskeleti — monorepo, Docker Compose, CI, lint, `healthz` | ✅ |
| **M1** | Kimlik, rıza, çocuk profili — auth, ebeveyn kaydı, eşleştirme | ✅ |
| M2–M8 | LLM Gateway, ipucu merdiveni, istemci, paneller, yayın | ⏳ |

## Mevcut özellikler (M1)

- **Ebeveyn/öğretmen kaydı** — parola `argon2` ile, JWT `access` + `refresh` (rotasyonlu, logout'ta iptal).
- **Çocuk profili** — takma ad + doğum yılı + sınıf; e-posta/telefon **tutulmaz**.
- **Amaç bazlı rıza** (`service`, `analytics`, `llm_processing`, `photo_processing`) — `service` rızası yoksa çocuk oturumu açılamaz.
- **Cihaz eşleştirme** — tek kullanımlık kod (hash'li, 10 dk, 5 deneme limiti).
- **Nesne düzeyi yetki** — ebeveyn yalnızca kendi çocuğunun verisini görür.

## Teknoloji

| Katman | Yığın |
|---|---|
| Backend | FastAPI · Python 3.12 · SQLAlchemy 2 + Alembic · PostgreSQL · Redis |
| İstemci | Flutter (iOS + Android + Web, tek proje) — yakında |
| Kalite | pytest · ruff · mypy · GitHub Actions CI |

## Hızlı başlangıç (Docker)

```powershell
docker compose up --build
```

```powershell
curl http://localhost:8000/healthz   # {"status":"ok",...}
curl http://localhost:8000/readyz    # db+redis hazırsa 200, değilse 503
```

- API dokümanı (OpenAPI): <http://localhost:8000/docs>

## Yerel geliştirme (Docker'sız)

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

DB entegrasyon testlerini de çalıştırmak için (Postgres `localhost:5432`'de olmalı):

```powershell
$env:TEST_DATABASE_URL = "postgresql+asyncpg://hint:hint@localhost:5432/hint"
pytest
```

## Komutlar

| Komut | Açıklama |
|---|---|
| `make up` / `make down` | Yerel ortamı başlat / durdur |
| `make test` | Birim + entegrasyon testleri |
| `make lint` | `ruff` + `mypy` |
| `make eval` / `make migrate` | Eval / Alembic migrasyon |
| `make client-gen` / `make client-test` | OpenAPI'den Dart istemcisi / Flutter testleri |

## Repo yapısı

```
hint-ai/
├─ apps/
│  ├─ api/        # FastAPI (kimlik, rıza, çocuk profili)
│  ├─ client/     # Flutter (iOS/Android/Web) — planlanıyor
│  ├─ landing/    # Statik landing — planlanıyor
│  └─ worker/     # Arka plan işleri — planlanıyor
├─ docs/          # Bölümlere ayrılmış plan + milestone'lar
├─ evals/         # Golden / adversarial / safety setleri
├─ infra/         # Docker, CI
└─ docker-compose.yml
```

## Dokümantasyon

- [docs/INDEX.md](docs/INDEX.md) — bölüm indeksi ve milestone → bölüm eşlemesi
- [AGENTS.md](AGENTS.md) — AI asistanı talimatları
- [DECISIONS.md](DECISIONS.md) · [ASSUMPTIONS.md](ASSUMPTIONS.md)

## Güvenlik & gizlilik

Bu proje çocuk verisi işler: cevap değil ipucu verir, PII LLM'e gitmeden maskelenir, reklam ve üçüncü taraf izleme yoktur. Detay: [docs/sections/10-guvenlik-uyum.md](docs/sections/10-guvenlik-uyum.md)
