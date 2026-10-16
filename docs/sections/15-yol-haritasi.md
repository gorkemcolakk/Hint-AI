## 15. Yol Haritası

> Hafta sayıları ders takvimine göre kaydırılır. Önce **teslim tarihlerini** (ara sunum, final, demo) buraya yazın.

### 15.1 Fazlar

| Faz | Süre (öneri) | Amaç | Çıktı |
|---|---|---|---|
| **Faz 0: Hizalama ve keşif** | Hafta 1–2 | Segment kararı, görüşmeler, rakip analizi | `DECISIONS.md`, 15 görüşme planı, rakip matrisi |
| **Faz 1: Doğrulama + prototip** | Hafta 3–5 | Varsayımları test et, tıklanabilir prototip, landing page | Fake-door sonuçları, Figma prototip, mini hint engine (CLI/notebook) |
| **Faz 2: MVP çekirdeği** | Hafta 6–9 | Çalışan uçtan uca akış (matematik) | Ebeveyn kayıt→çocuk→ipucu→rapor, eval raporu v1 |
| **Faz 3: Pilot** | Hafta 10–12 | 1–2 öğretmen / 10–20 öğrenci (izinli) | Pilot verisi, etki deneyi, düzeltmeler |
| **Faz 4: Sunum ve ölçekleme planı** | Hafta 13–14 | Finans, pitch, demo, yol haritası | Final dosyası, demo videosu, pitch deck |

### 15.2 Teknik milestone'lar (AI asistanı için sıralı)

| # | Milestone | İş paketi | Kabul kriterleri |
|---|---|---|---|
| **M0** | Altyapı iskeleti | Monorepo, Docker Compose (api, db, redis), CI, lint, `healthz`, ortam değişkeni şablonu | `docker compose up` ile çalışır; CI yeşil |
| **M1** | Kimlik, rıza, çocuk profili | Auth, ebeveyn kaydı, çocuk profili, rıza kayıtları, cihaz eşleştirme | Rıza olmadan çocuk oturumu açılamaz (test) |
| **M2** | LLM Gateway + PII maskeleme | Sağlayıcı soyutlama, retry/timeout, maliyet kaydı, maskeleme | Maskeleme birim testleri; sahte sağlayıcı ile entegrasyon testi |
| **M3** | Gizli çözüm + SymPy doğrulama | Sınıflandırma, çözüm üretimi, doğrulama | Golden set'te doğrulama oranı raporlanır |
| **M4** | İpucu merdiveni + sızıntı kontrolü | L0–L4, escalation, kural + yargıç sızıntı kontrolü | Golden set'te L0–L3 sızıntı < %1 (hedef); regresyon testleri |
| **M5** | Güvenlik katmanı | Girdi/çıktı moderasyonu, kriz akışı, injection seti | Adversarial setin ≥ %98'i atlatılamaz |
| **M6** | Flutter çocuk modu (mobil + web) | Flutter akışı (mobil + web), yaş temaları, erişilebilirlik | Aynı akış hem mobil hem web e2e testinden geçer; kullanılabilirlik testi notları |
| **M7** | Flutter ebeveyn modu + rapor + faturalama | Panel, haftalık rapor, abonelik, kota | Rapor doğruluğu testi, webhook idempotency |
| **M8** | Flutter öğretmen modu + eval otomasyonu + yayın hazırlığı | Sınıf, ısı haritası, CI'da eval, gözlemlenebilirlik, güvenlik gözden geçirme | Eval CI'da, runbook'lar, pentest bulguları kapatılmış |

### 15.3 Paralel iş akışları

- **İş/Pazar:** görüşmeler, fiyat testi, pilot anlaşmaları, finansal model.
- **Hukuk:** aydınlatma metni, rıza metinleri, gizlilik politikası, veri işleme envanteri.
- **İçerik:** kazanım listesi, golden set, misconception kütüphanesi (öğretmenlerle).
- **Marka/Tasarım:** isim/logo doğrulaması (marka tescil taraması), tasarım sistemi.
- **Landing:** landing page (statik/basit site, SEO ve ön kayıt).

---

