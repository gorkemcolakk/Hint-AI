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
| **M2.1** | Gateway sertleştirme (maskeleme yanlış pozitifleri, fail-closed rıza, ayrı test DB) | ✅ tamam |
| **M3** | Gizli çözüm + SymPy doğrulama | ✅ tamam (gerçek model: 22/22 doğru, kısmi ölçüm) |
| **M4** | İpucu merdiveni (L0–L4) + sızıntı kontrolü | 🟡 prototip: kural + LLM yargıç çalışıyor; gerçek modelle yalnızca 1 soru ölçüldü (v2 prompt ölçümü bekliyor) |
| **M5** | Güvenlik katmanı ve moderasyon (kriz yönlendirmesi, injection) | 🟡 prototip: kural tabanlı sınıflandırıcı; kriz metinleri uzman onayı bekliyor |
| **M6** | Expo çocuk modu (öğrenme akışı, yaş temaları) | 🟡 prototip: web'de çalışıyor; mobil ve e2e test yok |
| **M7** | Expo ebeveyn modu (raporlar, kota, faturalama) | 🟡 prototip: uygulama içi özet; e-posta raporu ve faturalama yok |
| **M8** | Expo öğretmen modu (sınıf paneli, ısı haritası) | 🟡 prototip: sınıf, davet kodu, veli onayı, ısı haritası; MEB kazanım eşlemesi yok |
| **M9** | Eval otomasyonu, gözlemlenebilirlik ve yayın hazırlığı | ⏳ bekliyor |

M4–M8 prototipi tek bir dikey dilim olarak yapıldı (sıra ve gerekçe: [docs/mvp-plan.md](docs/mvp-plan.md)). Gerçek çocuklarla kullanım için ücretli LLM katmanı, uzman/hukuk onayları ve gerçek model ölçümü gerekir.

## Prototipte eklenenler (M4–M8)

- **İpucu merdiveni** — `POST /v1/problems/{id}/hints`, `POST /v1/problems/{id}/attempts`, `GET /v1/problems/{id}`. L0–L4 (L5 kapalı); "takıldım", 2 yanlış deneme ve zorlanma ifadesiyle yükselme; doğrulanamayan soruda temkinli üst sınır. Cevap SymPy ile kontrol edilir, doğru cevap hiçbir yanıtta dönmez.
- **Sızıntı kontrolü** — kural katmanı (rakam, kesir, ondalık, yazıyla sayı, kök, "x = …" kalıpları; L0–L2'de ara sonuçlar) + LLM yargıç (`judge_v2`). Yargıç hatası/belirsizliği sızıntı sayılır; sızıntıda en fazla 3 üretim, yargıç 2 kez reddederse soru türüne uygun hazır ipucu.
- **Girdi/çıktı güvenliği** — kriz (kendine zarar, istismar) metni LLM'e gitmez ve saklanmaz; sabit destek mesajı + 112 / ALO 183. "Cevabı söyle" girişimleri not ile işlenir. Model çıktısında kişisel veri, bağlantı, uygunsuz içerik varsa yeniden üretilir. Olaylar `moderation_events`'te (metin yok).
- **Ebeveyn özeti** — `GET /v1/children/{id}/summary`: çözülen, ipucusuz çözülen, ortalama ipucu, konular, son sorular, güvenlik uyarıları. Varsayılan gizlilikte soru metni yok; istismar bildirimleri ebeveyne gösterilmez.
- **Öğretmen paneli** — sınıf + davet kodu; veli kodu önizleyip onaylayarak çocuğu kaydeder ya da çıkarır. Konu × öğrenci ısı haritası; öğretmen soru/ipucu metnini ve güvenlik uyarılarını görmez.
- **Eval** — `python -m evals.run_safety_eval` (adversarial set), `python -m evals.run_hint_eval [--real --ids 1,2]` (ipucu sızıntısı).

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
