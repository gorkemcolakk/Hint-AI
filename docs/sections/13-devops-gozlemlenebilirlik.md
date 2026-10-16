## 13. DevOps, Gözlemlenebilirlik, Test

### 13.1 CI/CD

- `main` korumalı, PR zorunlu, en az 1 onay.
- Pipeline: lint (ruff/flake8) → tip kontrol (mypy) → birim test → entegrasyon test → güvenlik taraması (SAST, SCA, secret scan) → **eval smoke seti** → `flutter analyze` → `flutter test` → web + Android build (matris) → imaj build → staging deploy → e2e → manuel onay → prod.
- Veritabanı migrasyonları (Alembic), geri alınabilir, expand/contract deseni.
- Feature flag: yeni ipucu stratejileri/prompt'lar kademeli açılır.
- Hızlı geri alma (rollback) planı.

### 13.2 Test piramidi

| Katman | Kapsam |
|---|---|
| Birim | İpucu seviye mantığı, escalation, sızıntı kural kontrolü, PII maskeleme, SymPy doğrulama, politika kilidi |
| Entegrasyon | API + DB + Redis, LLM gateway (sahte sağlayıcı ile), webhook'lar |
| Sözleşme (contract) | Frontend ↔ API OpenAPI şeması |
| E2E | Kritik akışlar: ebeveyn kayıt → rıza → çocuk eşleştirme → soru → ipucu → çözüm; abonelik. Flutter integration_test ile hem web hem mobilde |
| AI eval | Bölüm 11 |
| Yük | Eşzamanlı oturum, SSE bağlantıları, LLM gecikme simülasyonu |
| Güvenlik | OWASP, yetki atlama, injection setleri |
| Erişilebilirlik | Otomatik + manuel tarama |
| Kullanılabilirlik | Gerçek çocuklarla gözlem (etik izinle) |

### 13.3 Gözlemlenebilirlik

- **Log:** Yapılandırılmış (JSON), **PII yok** (çocuk metni loglanmaz, yalnızca kimlikler ve meta).
- **Metrik:** İstek gecikmesi, hata oranı, LLM gecikme/maliyet, sızıntı kontrolü başarısızlık oranı, moderasyon tetiklenme oranı, aktif oturum.
- **İz (trace):** İpucu boru hattının her adımı için (OpenTelemetry).
- **Alarm:** Maliyet aşımı, sızıntı oranı artışı, moderasyon servis hatası, 5xx artışı, LLM sağlayıcı hata oranı.
- **Ürün analitiği:** Çocuk tarafında üçüncü taraf izleme yok; sunucu tarafı olay kaydı, anonimleştirilmiş.
- **Durum sayfası** (pilot okullar için güven).

### 13.4 Operasyon

- Runbook'lar: LLM kesintisi, veri tabanı geri yükleme, güvenlik olayı, yanlışlıkla cevap sızıntısı (acil prompt geri alma).
- Nöbet (on-call) rotasyonu (öğrenci ekibi için basit, pilot dönemi için).
- Değişiklik günlüğü (CHANGELOG), sürüm notları.

---

