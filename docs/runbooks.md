# Hint.ai Operasyon Runbook'ları

> Kaynak: Bölüm 13.4 · Pilot ve canlı ortam müdahale rehberi. Çocuk metinleri log'larda veya veritabanı olaylarında yer almaz; incelemeler yalnızca `request_id`, `problem_id` ve `llm_call_id` üzerinden yürütülür.

---

## 1. LLM Sağlayıcı Kesintisi, Zaman Aşımı veya Kota Dolumu

### Belirtiler
- `/v1/problems` uç noktasında `503` oranının artması veya `llm_calls` tablosunda `LLMTimeoutError` / `LLMServerError` / `LLMRateLimitError` kayıtları.
- İpucu isteklerinde `hints.source = 'fallback'` oranının yükselmesi.

### Sistemin Otomatik Davranışı
- **Yeni soru (`POST /v1/problems`):** Sağlayıcı erişilemiyorsa kullanıcıya nazik `503` mesajı döner.
- **İpucu (`POST /v1/problems/{id}/hints`):** Açık sorularda öğrenci yarı yolda kalmaz; otomatik olarak sızıntısız `fallback` ipucuna düşer (L4'te doğrulanmış çözümlü ikiz örnek kullanılır).
- **Günlük kota (`429`):** Çocuk ekranında sıfır maliyetli *Kendi Kendine Kontrol Listesi* açılır.

### Müdahale Adımları
1. Sağlayıcı durumunu ve model yanıt süresini kontrol edin (ör. `gemini-3.6-flash` yoğunluk yaşıyorsa `LLM_MODEL=gemini-2.5-flash` ve `LLM_JUDGE_MODEL=gemini-3.5-flash-lite` ayarına geçin).
2. Maliyet/kota patlaması varsa `LLM_DAILY_CALL_LIMIT_PER_CHILD` değerini geçici olarak düşürün.
3. Servis tamamen devre dışıysa kesinti süresince durumu okul/veli iletişim kanalından paylaşın; açık sorular `fallback` ipuçları ve SymPy cevap doğrulamasıyla çalışmaya devam eder.

---

## 2. Yanlışlıkla Cevap Sızıntısı — Acil Prompt Geri Alma (Rollback)

### Belirtiler
- Eval raporunda veya kullanıcı bildiriminde bir ipucunun L0–L4 seviyesinde nihai cevabı açık ya da dolaylı ele vermesi.

### Müdahale Adımları
1. `hints` tablosundan ilgili `problem_id` kaydının `prompt_version` ve `leak_check` JSON alanını inceleyin (`rule_pass` mi kaçırdı, `judge` mı `leak: false` dedi?).
2. Yeni prompt sürümünden kaynaklanıyorsa `apps/api/app/modules/tutoring/service.py` içindeki `HINT_PROMPT` (veya `judge.py` içindeki `JUDGE_PROMPT`) sabitini bir önceki kararlı sürüme (`hint_v2` / `judge_v2`) çekip deploy edin (eski prompt dosyaları silinmediği için anında geri alınabilir).
3. Kaçan kalıbı `apps/api/tests/test_leak.py` ve `evals/data/` setine regresyon testi olarak ekleyin; `make eval` ve `pytest` yeşil olmadan yeni prompt sürümü yayınlamayın.

---

## 3. Çocuk Güvenliği ve Kriz Olayı Müdahalesi

### Belirtiler
- `moderation_events` tablosunda `severity >= 3` (`self_harm` veya `abuse_disclosure`) kaydı oluşması.

### Kritik Kurallar (Değiştirilemez)
- Kriz girdileri LLM'e **gönderilmez** ve ham metin veritabanına/loglara **yazılmaz**.
- Uygulama çocuğa anında sabit destek kartını (`112` Acil ve `ALO 183` Sosyal Destek) gösterir.
- **`self_harm`:** `notify_guardian = true` olarak işaretlenir ve ebeveyn özetinde sakin rehberlik mesajıyla görünür.
- **`abuse_disclosure`:** Zarar veren kişi ebeveyn olabileceği için ebeveyne **KESİNLİKLE gösterilmez** (`GUARDIAN_HIDDEN_CATEGORIES`, KVKK `export` paketinde de yer almaz). Yalnızca yetkili çocuk koruma/hukuk sorumlusu prosedürüyle incelenir (⚠️ Pilot öncesi hukuk/uzman protokolü imzalanmalıdır).

---

## 4. Veritabanı Yedekleme, Geri Yükleme ve KVKK Veri Talepleri

### Yedekleme ve Geri Yükleme Testi
- Yedek alma: `pg_dump -Fc -h <host> -U hint -d hint -f hint_$(date +%F).dump`
- Geri yükleme doğrulaması (ayrı test veritabanına): `pg_restore -h <host> -U hint -d hint_restore_check hint_<tarih>.dump` ardından `alembic current` ve `/readyz` kontrolü.

### KVKK Taşıma ve Silme Talepleri
- **Veri dışa aktarma:** Ebeveyn panelinden veya `GET /v1/children/{child_id}/export` ucuyla JSON olarak indirilir (`summary_only` gizlilik düzeyi korunur, gizli çözümler ve gizli moderasyon kategorileri dahil edilmez).
- **Profil ve veri silme:** Ebeveyn panelinden çift onayla veya `DELETE /v1/children/{child_id}` ucuyla çalıştırılır. `child_profiles` silindiğinde `consents`, `pairing_codes`, `problems`, `hints`, `attempts`, `moderation_events` ve `enrollments` kayıtları `ON DELETE CASCADE` ile kalıcı olarak silinir; `llm_calls.child_id` alanı `SET NULL` yapılarak kişisel bağ koparılır.
