# Varsayımlar

> docs/master-plan.md Bölüm 20'de olmayan belirsiz kararlarda yapılan varsayımlar burada tutulur.

- M0'da `GET /healthz` (canlılık) her zaman 200 döner; `GET /readyz` (hazırlık) DB + Redis erişimini kontrol eder, hazır değilse 503 döner.
- M0 kapsamı yalnızca altyapıdır; kimlik, veri modeli ve moderasyon M1'den itibaren eklenir.
- Yerel makinede Docker yoksa `docker compose up` yerine API `uvicorn` ile, testler `pytest` ile doğrulanır.
- `make` hedefleri Linux/macOS/CI içindir; Windows'ta doğrudan `docker compose` ve `python -m` komutları kullanılır.
