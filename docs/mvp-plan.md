# Hint.ai MVP Planı (yeniden sıralama)

> Tarih: 2026-11-21 · Durum: A0–A4 + öğretmen paneli (minimal) prototip olarak yapıldı; A5 ve gerçek model ölçümü bekliyor
> Kaynak: docs/sections/05, 06, 07, 11, 15, 19 ve mevcut kod (M0–M3 bitti).

## 1. Neden yeniden sıralıyoruz

Mevcut sıra M4 (ipucu) → M5 (güvenlik) → M6 (çocuk ekranı) → M7 (ebeveyn) → M8 (öğretmen).
Bu sırayla gidilirse:

- **Ekranda görülen ilk ipucu M6'da gelir.** İki tam milestone boyunca ürünün asıl vaadi kimseye gösterilemez; demo, pitch ve kullanıcı görüşmeleri (Bölüm 19) bekler.
- **İpucu kalitesi ekransız ayarlanamaz.** "İpucu bıkkınlığı" (çocuğun sıkılıp bırakması, Bölüm 1'deki kritik eksik #4) ancak akış kullanılınca görülür. Prompt'u akışı deneyerek ayarlamak, sadece eval tablosuna bakmaktan daha hızlı sonuç verir.
- **Ücretsiz LLM kotası tam eval'i yavaşlatıyor** (M3'te günde ~20 istek, ölçüm 22/60 soruda kaldı). M5'i tam bitirmeden ilerlememek takvimi kotaya bağlar.

Tersi de doğru değil: **"önce sadece görüntü, güvenlik sonra" da yapılamaz.** AGENTS.md'deki değişmez kurallar (cevap verilmez, her LLM çıktısı sızıntı kontrolünden geçer) ilk ipucundan itibaren geçerli. Ürünün ana farkı cevap sızdırmamak. Sızıntı kontrolü olmadan yapılan bir demo, ürünün iddiasını göstermiş olmaz.

## 2. Karar: dikey dilim + güvenlik kapıları

Her aşamada **uçtan uca çalışan ince bir dilim** çıkarılır: backend + ekran birlikte. Güvenlik iki parçaya ayrılır:

- **Her zaman açık (ucuz, deterministik):** PII maskeleme (var), rıza kontrolü (var), kural tabanlı sızıntı kontrolü + güvenli yedek ipucu, L5 (tam çözüm) kapalı. Bunlar ilk ipucuyla birlikte gelir.
- **Gerçek çocuktan önce zorunlu (A3 kapısı):** LLM yargıç, injection/"cevabı söyle" tespiti, kriz akışı, adversarial eval. **A3 bitmeden ve ücretli LLM katmanına geçilmeden (D5) gerçek çocuk uygulamayı kullanmaz.** O zamana kadar yalnızca ekip ve sentetik verilerle çalışılır.

## 3. Yeni aşamalar

Efor: S = birkaç gün, M = ~1 hafta, L = 1–2 hafta (tek geliştirici için kaba tahmin).

| # | Aşama | Kapsam | Kabul kriteri | Eski M | Efor |
|---|---|---|---|---|---|
| **A0** | Docker'sız yerel ortam | Bölüm 4'teki kurulum, Redis isteğe bağlı, `scripts/dev.ps1`, demo verisi (seed), gerçekçi sahte ipucu veren mock LLM | Yeni bir Windows makinede README adımlarıyla API + web istemcisi açılır; pytest yeşil | — | S |
| **A1** | İpucu çekirdeği | `hints` + `attempts` tabloları, sorunun öğretim durumu (`current_hint_level`, open/solved); `hint_v1.md` prompt'u (L0–L4, yaşa göre ton); `POST /v1/problems/{id}/hints` (önce JSON), `POST /v1/problems/{id}/attempts` (SymPy ile cevap kontrolü); seviye atlama kuralları (takıldım, 2 yanlış, zorlanma sinyali; doğru adımda geri düşme); **kural tabanlı sızıntı kontrolü** + en fazla 2 yeniden üretim + seviye başına hazır yedek ipucu; düşük güvenli sorularda temkinli mod; L5 kapalı | Mock ile entegrasyon testleri; sızan ipucu örneklerini yakalayan birim testleri; hiçbir yanıtta `final_answer` olmadığını gösteren test | M4 (çekirdek) | M |
| **A2** | Çocuk ekranı — **ilk demo** | Expo'da (önce web): soru yaz → ipucu kartı + seviye göstergesi → "takıldım" → cevap gönder → doğru/yanlış geri bildirim → ölçülü kutlama; yükleniyor/hata/kota bitti durumları; iki yaş teması (Keşif 7–12, Odak 13–17); erişilebilirlik etiketleri | Demo senaryosu adım 1–3 (Bölüm 19.2) web'de baştan sona çalışır; Jest testleri; telefonda Expo Go ile bir kez denenir | M6 (çekirdek) | M |
| **A3** | Güvenlik asgarisi — **gerçek çocuk kapısı** | LLM yargıç (küçük model, yalnızca kural kontrolünü geçen ipuçlarına); girdide "cevabı söyle"/injection tespiti → yönlendirme; kriz kelimeleri → LLM'e gitmeyen sabit güvenli yanıt + olay kaydı; basit çıktı güvenliği; adversarial set v1 (~50 vaka); sızıntı eval çalıştırıcısı | Golden set örnekleminde L0–L3 sızıntı < %1 (örneklem büyüklüğüyle raporlanır); adversarial ≥ %98; demo adım 4 (manipülasyon denemesi) çalışır | M4 (yargıç) + M5 (kritik kısım) | M–L |
| **A4** | Ebeveyn görünümü | Çocuk detay ekranında özet: çözülen soru sayısı, bağımsız çözüm oranı (kuzey yıldızı metriği, Bölüm 18.1), ortalama ipucu seviyesi, konu listesi. Uygulama içi; e-posta ve ödeme yok | Rapor doğruluk testi; demo adım 5 çalışır | M7 (lite) | S–M |
| **A5** | Pilot hazırlığı | Ücretli LLM katmanı (D5), login rate limit (M1-1), kalan golden set ölçümü (#24–60), ipucu akışı SSE, web + mobil e2e, kullanılabilirlik testi notları; öğretmen ısı haritası (minimal, isteğe bağlı) | Bölüm 15 Faz 3 pilotu başlatılabilir | M5 kalan + M6/M8 kısmı | L |

**Demo hazır olma noktaları:** A2 sonunda iç demo (ekip, hoca) yapılabilir; A3 sonunda güvenlik gösterisi de eklenir; A4 sonunda Bölüm 19.2 senaryosunun 1–5. adımları tamamlanır.

## 4. Docker'sız yerel geliştirme (A0)

Docker Compose ve CI olduğu gibi kalır; yerel çalışma için ek bir yol açılır.

| Bileşen | Yerelde | Not |
|---|---|---|
| PostgreSQL 16 | venv içindeki `pixeltable-pgserver` paketi (PostgreSQL 16.15 binary'leri içinde); `scripts/localdb.py` veriyi `.local/pgdata`'da tutar, 127.0.0.1:5432'de açar, `hint` + `hint_test` veritabanlarını hazırlar. Sisteme kurulum veya yönetici izni yok | CI ve prod ile aynı veritabanı. SQLite önerilmez: modeller JSONB kullanıyor, migration'lar ve test altyapısı Postgres'e özel; CI'dan sapma yaratır |
| Redis | **Gerekmez** | Kodda yalnızca `/readyz` kullanıyor; `HINT_REDIS_URL` boşsa kontrol atlanır |
| API | `uv` ile sanal ortam + `pip install -e ".[dev]"`, `alembic upgrade head`, `uvicorn app.main:app --reload` | Yerelde Python 3.13, CI'da 3.12; ikisi de destekleniyor (`>=3.12`) |
| İstemci | `npm install` + `npm run web` | Node 22 kurulu |
| LLM | Varsayılan `LLM_PROVIDER=mock` | Ekran geliştirme ve testler kotayı hiç harcamaz |
| `make` | Yok → `scripts/dev.ps1` | `setup`, `api`, `web`, `test`, `lint`, `seed` alt komutları |

**Seed:** demo ebeveyni + çocuk + tüm rızalar + eşleştirme bağlantısını tek komutla hazırlar. Her denemede kayıt ve eşleştirme adımlarını tekrar yapmak gerekmez.

## 5. LLM kota stratejisi

Bir sorunun maliyeti yaklaşık olarak: çözüm 1–2 çağrı + ipucu başına 1 çağrı + yargıç 1 çağrı (A3'ten sonra). 4 ipuçlu bir soru ≈ 10 çağrı. Ücretsiz katmanda bu günde 2 tam soru demek.

- Ekran ve akış geliştirme **her zaman mock** ile yapılır. Mock, sorunun gizli çözümünden seviyeye uygun şablon ipuçları üretir.
- Gerçek model yalnızca prompt ayarı ve eval için kullanılır. Çözüm önbelleği (M3) aynı soruda çözüm çağrısını sıfırlar.
- Yargıç yalnızca kural kontrolünü geçen ipuçlarında çalışır.
- Sızıntı eval'i örneklemle yapılır (ör. 20 soru × L0–L3) ve birkaç güne yayılır; rapor örneklem büyüklüğünü açıkça yazar.
- Her ekip üyesi kendi geliştirme anahtarını kullanabilir. Anahtar repoya girmez (Kural 5).
- Yargıç için daha ucuz bir model ve kotası ayrıca değerlendirilir (**doğrulanmalı**).

## 6. MVP dışında kalanlar (sonraya)

Fotoğraf/OCR (D10), abonelik ve ödeme (D11), e-posta ile haftalık rapor, tam öğretmen paneli, Elo/BKT öğrenci modeli, pgvector, misconception kütüphanesi (öğretmenlerle paralel içerik işi olarak büyür), landing sayfası (paralel iş akışı).

## 7. Bekleyen kararlar

| Karar | Öneri | Kim |
|---|---|---|
| D4 — "Çözümü göster" (L5) | MVP'de kapalı; politika kilidi sonra | Ürün + pedagoji |
| İpucu ilk sürümde SSE mi JSON mu | JSON; SSE A5'te (Bölüm 9.2 şeması korunur) | BM-1 + BM-2 |
| README'deki M9 satırı | Dokümanda M8'e kadar milestone var; bu planla birlikte A0–A5'e geçilir | BM-1 |
