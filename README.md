# Hint.ai 🎓

> Cevabı değil, kademeli ipucu veren AI öğrenme arkadaşı — 7–17 yaş.

![CI](https://github.com/gorkemcolakk/Hint-AI/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)

Hint.ai, öğrencinin takıldığı yeri tespit edip **cevabı söylemeden**, adım adım ipucu vererek kendi başına çözmesini sağlar. Ebeveyn paneli ve öğretmen paneliyle birlikte gelir.

## Durum

| Aşama / Milestone | Tanım | Durum |
|---|---|---|
| **M0–M3** | Altyapı, kimlik/rıza, Expo iskeleti, LLM Gateway + PII maskeleme, gizli çözüm + SymPy | ✅ tamam |
| **A0** | Docker'sız yerel ortam (`scripts/localdb.py`, `scripts/dev.ps1`, demo seed) | ✅ tamam |
| **A1** | İpucu çekirdeği (`L0–L4`, SymPy deneme kontrolü, kural tabanlı sızıntı + yedek ipucu) | ✅ tamam |
| **A2** | Expo çocuk modu (`Keşif` / `Odak` temaları, rahat okuma, matematik biçimlendirme, 429 kontrol listesi) | ✅ tamam |
| **A3** | Güvenlik katmanı (`hint_v3` + `judge_v3`, girdi/çıktı moderasyonu, kriz kartı, adversarial eval) | ✅ tamam *(kriz metinleri uzman/hukuk onayı bekliyor)* |
| **A4** | Ebeveyn paneli (ilerleme özeti, günlük sınır/gizlilik/politika ayarı, rıza yönetimi, KVKK veri indirme/silme) | ✅ tamam *(e-posta raporu ve ödeme Faz 2 sonrası)* |
| **Öğretmen (M8)** | Sınıf, davet kodu, veli onay önizlemesi, konu × öğrenci ısı haritası | ✅ tamam *(MEB kazanım kodu eşlemesi sonra)* |
| **A5** | Pilot ve yayın hazırlığı (SSE ipucu akışı, auth rate-limit, yapılandırılmış log, CI eval smoke, runbook'lar) | ✅ teknik altyapı tamam *(gerçek çocuk pilotu öncesi ücretli LLM katmanı ve uzman onayları gerekir)* |

A0–A5 dikey dilim planının ayrıntıları: [docs/mvp-plan.md](docs/mvp-plan.md) · Operasyon rehberleri: [docs/runbooks.md](docs/runbooks.md).

## Öne Çıkan Özellikler (A0–A5)

- **İpucu merdiveni ve SSE akışı** — `POST /v1/problems/{id}/hints` (JSON + `text/event-stream` SSE), `POST /v1/problems/{id}/attempts`, `POST /v1/hints/{id}/feedback`, `GET /v1/problems/{id}`. `hint_v3` ile L0–L2 sorunun sayılarıyla yönlendirir, L3 ilk adımı tamamlayıp tek son işlemi öğrenciye bırakır, L4 farklı sayılarla ikiz örnek çözer; L5 kapalıdır.
- **Sızıntı kontrolü** — kural katmanı (rakam, kesir, ondalık, yazıyla sayı, kök, `x = …` kalıpları; L0–L2'de ara sonuçlar) + LLM yargıç (`judge_v3`, ayrı hızlı yargıç modeli `LLM_JUDGE_MODEL` destekli). SSE akışında dahi yalnızca tüm kontrolleri geçmiş ipucu akıtılır.
- **Girdi/çıktı güvenliği ve hız sınırı** — kriz ifadeleri LLM'e gitmez ve saklanmaz; sabit destek kartı (`112` / `ALO 183`) döner. Giriş, kayıt ve eşleştirme uçlarında kayan pencereli brute-force rate limit (`429`) çalışır.
- **Ebeveyn kontrolleri ve KVKK hakları** — `GET /v1/children/{id}/summary`, `PATCH /v1/children/{id}` (günlük yeni soru sınırı `POST /v1/problems` üzerinde uygulanır), `POST /v1/children/{id}/consents`, `GET /v1/children/{id}/export` (JSON dışa aktarma) ve `DELETE /v1/children/{id}` (kademeli kalıcı silme). İstismar bildirimleri ebeveyn özetinde ve dışa aktarımda gizlenir.
- **Öğretmen paneli** — sınıf + davet kodu kopyalama/paylaşma; veli kodu önizleyip onaylayarak çocuğu kaydeder ya da çıkarır. Konu × öğrenci ısı haritası; öğretmen soru/ipucu metnini ve güvenlik uyarılarını görmez.
- **Gözlemlenebilirlik ve Eval otomasyonu** — gövde/sorgu loglamayan JSON `StructuredLoggingMiddleware` (`X-Request-ID`), `docs/runbooks.md`, CI üzerinde otomatik `run_pii_eval`, `run_safety_eval`, `run_solution_eval` ve `run_hint_eval` smoke kontrolleri.

## Mevcut özellikler (M1 + M1.5 + M2 + M3)

- **Expo istemcisi (iOS + Android + Web, tek kod tabanı)** — ebeveyn kaydı ve girişi, çocuk listesi, amaç bazlı rıza kutularıyla (önceden işaretsiz) çocuk ekleme, tek kullanımlık eşleştirme bağlantısı ve çocuk modunda karşılama ekranı.
- **Tipli API istemcisi** — FastAPI'nin OpenAPI şemasından `openapi-typescript` ile üretilir; şemanın ve tiplerin koddan sapmadığı CI'da kontrol edilir.
- **İstemci oturum güvenliği** — token mobilde `expo-secure-store`'da, web'de yalnızca bellekte; ebeveyn token'ı bitmeden tek bir yenileme çağrısıyla yenilenir; cihaz çocuk moduna geçince ebeveyn oturumu sunucuda iptal edilir.
- **Ebeveyn/öğretmen kaydı** — parola `argon2` ile, JWT `access` + `refresh` (rotasyonlu, logout'ta iptal).
- **Çocuk profili** — takma ad + doğum yılı + sınıf; e-posta/telefon **tutulmaz**.
- **Amaç bazlı rıza** (`service`, `analytics`, `llm_processing`, `photo_processing`) — `service` rızası olmadan çocuk oturumu açılamaz, `llm_processing` rızası olmadan LLM çağrısı yapılamaz.
- **Cihaz eşleştirme** — tek kullanımlık kod (hash'li, 10 dk geçerlilik, 5 hatalı deneme sınırı).
- **LLM Gateway & Sağlayıcı soyutlaması** — OpenAI uyumlu genel HTTP sağlayıcısı (Google Gemini) ve testler için `MockLLMProvider`.
- **KVKK uyumlu PII maskeleme** — TCKN (checksum doğrulamalı), TR telefon, e-posta, TR IBAN ve sezgisel ad/okul kalıpları sağlayıcıya gitmeden maskelenir. "adım" (step) gibi ifadeler isim sanılmaz; uygulamanın kendi system prompt'ları (`TrustedText`) maskelenmez.
- **Fail-closed rıza** — çocuk verisi işleyebilecek her LLM çağrısı çocuk bağlamı ister; bağlam yoksa çağrı yapılmaz.
- **Gizlilik ve maliyet izleme** — `llm_calls` tablosunda ve loglarda çocuk metni/prompt tutulmaz; token ve maliyet izlenir, çocuk başına günlük çağrı limiti uygulanır.
- **Gizli çözüm + SymPy doğrulama** — `POST /v1/problems`: soru maskelenip kaydedilir, LLM yapılandırılmış çözüm üretir, SymPy cevabı bağımsız kontrol eder (tutmazsa bir kez yeniden üretilir, yine tutmazsa düşük güven). Çözüm öğrenciye dönmez; doğrulanan çözümler aynı soru için önbellektir. LLM çıktısı SymPy'a güvenli ayrıştırmayla girer.
- **Eval çalıştırıcısı** — `make eval`: 31 sentetik vakada PII sızıntısı ve yanlış pozitif; 60 soruluk 5–8. sınıf golden set'te SymPy doğrulama oranı ve cevap doğruluğu (`python -m evals.run_solution_eval --real` gerçek modelle; son rapor: [evals/reports](evals/reports/2026-11-16-solve_v1-gemini-3.6-flash.md)).

## Teknoloji

| Katman | Yığın |
|---|---|
| Backend | FastAPI · Python 3.12 · SQLAlchemy 2 + Alembic · PostgreSQL · Redis |
| İstemci | Expo SDK 58 · React Native + Web · TypeScript · Expo Router · TanStack Query (iOS + Android + Web, tek proje) |
| Kalite | pytest · ruff · mypy (strict) · Jest + Testing Library · ESLint · GitHub Actions CI |

## Nasıl çalıştırılır

### 0. Docker'sız (Windows, yalnızca Python + Node)

PostgreSQL 16, venv içindeki `pixeltable-pgserver` paketinden gelir; sisteme kurulum gerekmez. `apps/api/.env.example`'ı `.env` olarak kopyalayıp veritabanı adreslerini `127.0.0.1:5432`, `HINT_REDIS_URL`'i boş yapın; kotasız deneme için `LLM_PROVIDER=demo`, demo giriş düğmeleri için `HINT_DEV_SHORTCUTS=true`.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 setup   # venv + npm (bir kez)
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 api     # DB + migration + API (:8000)
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 web     # ayrı terminalde istemci (:8081)
```

Diğer komutlar: `test`, `lint`, `seed`, `stop`. Veritabanı `.local/pgdata`'da durur (git'e girmez).

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

Postgres Compose üzerinde `localhost:5432` portunda açıkken. Testler tabloları boşalttığı için geliştirme veritabanını değil, adı `_test` ile biten ayrı bir veritabanını kullanır; `hint_test` yoksa ilk çalıştırmada oluşturulur.

```powershell
cd apps/api
$env:TEST_DATABASE_URL = "postgresql+asyncpg://hint:hint@localhost:5432/hint_test"
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
