# Hint.ai 🎓

> Cevabı değil, kademeli ipucu veren AI öğrenme arkadaşı — 7–17 yaş.

![CI](https://github.com/gorkemcolakk/Hint-AI/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)

Hint.ai, öğrencinin takıldığı yeri tespit edip **cevabı söylemeden**, adım adım ipucu vererek kendi başına çözmesini sağlar. Ebeveyn paneli ve öğretmen paneliyle birlikte gelir.

## Durum

| Milestone | Tanım | Durum |
|---|---|---|
| **M0** | Altyapı iskeleti (FastAPI, Docker Compose, CI, lint, `healthz`) | ✅ tamam |
| **M1** | Kimlik, rıza ve çocuk profili (Auth, ebeveyn kaydı, eşleştirme) | ✅ tamam |
| **M1.5** | Expo istemci iskeleti (React Native + Web, TypeScript, tek kod tabanı) | ✅ tamam |
| **M2** | LLM Gateway + PII maskeleme (Gemini/OpenAI uyumlu, rıza/kota, eval) | ✅ tamam |
| **M3** | Gizli çözüm + SymPy doğrulama | 🔜 sıradaki |
| **M4** | İpucu merdiveni (L0–L4) + sızıntı kontrolü | ⏳ bekliyor |
| **M5** | Güvenlik katmanı ve moderasyon (kriz yönlendirmesi, injection) | ⏳ bekliyor |
| **M6** | Expo çocuk modu (öğrenme akışı, yaş temaları) | ⏳ bekliyor |
| **M7** | Expo ebeveyn modu (raporlar, kota, faturalama) | ⏳ bekliyor |
| **M8** | Expo öğretmen modu (sınıf paneli, ısı haritası) | ⏳ bekliyor |
| **M9** | Eval otomasyonu, gözlemlenebilirlik ve yayın hazırlığı | ⏳ bekliyor |

## Mevcut özellikler (M1 + M1.5 + M2)

- **Expo istemcisi (iOS + Android + Web, tek kod tabanı)** — ebeveyn kaydı ve girişi, çocuk listesi, amaç bazlı rıza kutularıyla (önceden işaretsiz) çocuk ekleme, tek kullanımlık eşleştirme bağlantısı ve çocuk modunda karşılama ekranı.
- **Tipli API istemcisi** — FastAPI'nin OpenAPI şemasından `openapi-typescript` ile üretilir; şemanın ve tiplerin koddan sapmadığı CI'da kontrol edilir.
- **İstemci oturum güvenliği** — token mobilde `expo-secure-store`'da, web'de yalnızca bellekte; ebeveyn token'ı bitmeden tek bir yenileme çağrısıyla yenilenir; cihaz çocuk moduna geçince ebeveyn oturumu sunucuda iptal edilir.
- **Ebeveyn/öğretmen kaydı** — parola `argon2` ile, JWT `access` + `refresh` (rotasyonlu, logout'ta iptal).
- **Çocuk profili** — takma ad + doğum yılı + sınıf; e-posta/telefon **tutulmaz**.
- **Amaç bazlı rıza** (`service`, `analytics`, `llm_processing`, `photo_processing`) — `service` rızası olmadan çocuk oturumu açılamaz, `llm_processing` rızası olmadan LLM çağrısı yapılamaz.
- **Cihaz eşleştirme** — tek kullanımlık kod (hash'li, 10 dk geçerlilik, 5 hatalı deneme sınırı).
- **LLM Gateway & Sağlayıcı soyutlaması** — OpenAI uyumlu genel HTTP sağlayıcısı (Google Gemini) ve testler için `MockLLMProvider`.
- **KVKK uyumlu PII maskeleme** — TCKN (checksum doğrulamalı), TR telefon, e-posta, TR IBAN ve sezgisel ad/okul kalıpları sağlayıcıya gitmeden maskelenir.
- **Gizlilik ve maliyet izleme** — `llm_calls` tablosunda ve loglarda çocuk metni/prompt tutulmaz; token ve maliyet izlenir, çocuk başına günlük çağrı limiti uygulanır.
- **Eval çalıştırıcısı** — `apps/api/evals` altında sentetik çocuk veri setiyle çalışan sıfır PII sızıntı doğrulayıcısı.

## Teknoloji

| Katman | Yığın |
|---|---|
| Backend | FastAPI · Python 3.12 · SQLAlchemy 2 + Alembic · PostgreSQL · Redis |
| İstemci | Expo SDK 58 · React Native + Web · TypeScript · Expo Router · TanStack Query (iOS + Android + Web, tek proje) |
| Kalite | pytest · ruff · mypy (strict) · Jest + Testing Library · ESLint · GitHub Actions CI |

## Nasıl çalıştırılır

### 1. Docker Compose ile başlatma

```powershell
docker compose up -d --build
```

Canlılık ve hazırlık sağlık kontrolleri:
```powershell
curl http://localhost:8000/healthz   # {"status":"ok",...}
curl http://localhost:8000/readyz    # db+redis hazırsa 200, değilse 503
```

- OpenAPI / Swagger arayüzü: <http://localhost:8000/docs>

### 2. Veritabanı migrasyonları (Alembic)

```powershell
docker compose exec api alembic upgrade head
```

### 3. Testleri çalıştırma

Postgres Compose üzerinde `localhost:5432` portunda açıkken:

```powershell
cd apps/api
$env:TEST_DATABASE_URL = "postgresql+asyncpg://hint:hint@localhost:5432/hint"
pytest
```

Lint ve tip denetimi:
```powershell
ruff check .
mypy app tests evals
```

PII maskeleme ve sızıntı eval testi:
```powershell
python evals/run_pii_eval.py
```

### 4. İstemci (Expo)

API `localhost:8000`'de açıkken:

```powershell
cd apps/client
npm install
npm run web    # http://localhost:8081
npm start      # telefonda Expo Go ile açmak için QR kodu gösterir
```

Ayrıntılar (telefonda deneme, API adresi, testler): [apps/client/README.md](apps/client/README.md)

## Komutlar

| Komut | Açıklama |
|---|---|
| `make up` / `make down` | Yerel ortamı başlat / durdur |
| `make test` | Birim + entegrasyon testleri |
| `make lint` | `ruff` + `mypy` |
| `make eval` / `make migrate` | Eval / Alembic migrasyon |
| `make client-gen` / `make client-test` | OpenAPI'den TypeScript istemcisi / istemci testleri (Jest) |

## Repo yapısı

```
hint-ai/
├─ apps/
│  ├─ api/        # FastAPI (kimlik, rıza, çocuk profili)
│  ├─ client/     # Expo / React Native (iOS/Android/Web)
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
