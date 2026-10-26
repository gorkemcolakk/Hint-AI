## 7. Sistem Mimarisi

### 7.1 Üst seviye mimari

```mermaid
flowchart TB
  subgraph Clients
    A[Expo / React Native İstemcisi (iOS/Android/Web): çocuk / ebeveyn / öğretmen modları]
    D[Admin/Moderasyon Konsolu - ayrı mod veya basit web arayüzü]
  end

  subgraph Edge
    E[CDN + WAF + Rate Limit]
  end

  subgraph Backend
    F[API Gateway / BFF]
    G[Auth & Consent Service]
    H[Tutoring Service]
    I[Curriculum & Skill Service]
    J[Progress & Reporting Service]
    K[Billing Service]
    L[Notification Service]
    M[Moderation Service]
  end

  subgraph AI
    N[LLM Gateway]
    O[Hint Engine Orchestrator]
    P[Math Verifier - SymPy]
    Q[Safety Classifier]
    R[Leak Checker]
    S[OCR / Vision]
  end

  subgraph Data
    T[(PostgreSQL)]
    U[(Redis - cache, rate limit, session)]
    V[(Object Storage - görseller, raporlar)]
    W[(pgvector - kazanım/örnek arama)]
    X[(Queue - arka plan işleri)]
  end

  subgraph External
    Y[LLM Sağlayıcı(lar)]
    Z[Ödeme Sağlayıcı]
    AA[E-posta/Push]
  end

  A --> E --> F
  D --> E
  F --> G
  F --> H
  F --> J
  F --> K
  H --> O
  O --> S
  O --> Q
  O --> P
  O --> N
  O --> R
  N --> Y
  H --> I
  I --> W
  H --> T
  J --> T
  G --> T
  K --> Z
  L --> AA
  M --> T
  H --> U
  X --> J
  X --> L
```

### 7.2 Mimari stil: modüler monolit önerisi

6 kişilik öğrenci ekibi için **mikroservis aşırıdır.** Seçenekler:

| Seçenek | Artı | Eksi |
|---|---|---|
| **Modüler monolit** (tek deploy, net modül sınırları) | Basit operasyon, hızlı geliştirme, sonradan ayrıştırılabilir | Disiplin gerektirir |
| Mikroservis | Bağımsız ölçek | Operasyon ve debug yükü, ekip için fazla |
| Serverless fonksiyonlar | Düşük sabit maliyet | Soğuk başlatma, akış (streaming) zorlukları |

Bölüm 7.1'deki kutular **mantıksal modüllerdir.** MVP'de tek FastAPI uygulaması içinde paketler olarak yaşar, arayüzleri net olur.

### 7.3 Hint Engine boru hattı (sistemin kalbi)

```
Öğrenci girdisi (metin/foto)
   │
   ▼
[1] Girdi güvenlik/moderasyon (PII maskeleme, zararlı içerik, prompt injection tespiti)
   │
   ▼
[2] OCR (foto ise) + soru normalizasyonu
   │
   ▼
[3] Soru sınıflandırma: ders, sınıf, konu, kazanım (küçük/ucuz model + kural)
   │
   ▼
[4] GİZLİ ÇÖZÜM üretimi (LLM) + DOĞRULAMA (SymPy ile sayısal/cebirsel kontrol)
   │      → çözüm adımları + nihai cevap yapılandırılmış JSON olarak saklanır (öğrenciye GÖSTERİLMEZ)
   ▼
[5] Öğrenci durumu: mevcut ipucu seviyesi, önceki denemeler, beceri puanı, yaş bandı
   │
   ▼
[6] İPUCU üretimi (LLM): girdi = soru + gizli çözüm + seviye + yaş tonu + konuşma geçmişi
   │
   ▼
[7] SIZINTI KONTROLÜ (Leak Checker): 
   │      a) Kural: nihai cevap/ara kritik değerler metinde geçiyor mu? (regex/sembolik eşleşme)
   │      b) LLM yargıç (küçük model): "bu ipucu cevabı ele veriyor mu?"
   │      → sızıntı varsa yeniden üret (max N), yine olursa güvenli yedek ipucu
   ▼
[8] Çıktı güvenliği: yaşa uygunluk, toksisite, kişisel veri
   │
   ▼
[9] Yanıtı akış (stream) ile gönder + kayıt (llm_calls, hints, moderasyon olayları)
```

**Kritik tasarım kararları:**
- **Gizli çözüm ayrı bir adımdır.** İpucu üreticisi çözümü "bilir" ama kuralı bellidir: seviyeye göre ne kadar açabileceği. Bu, ipuçlarının doğru olmasını sağlar (cevabı bilmeyen model yanlış ipucu verebilir).
- **Sızıntı kontrolü deterministik + LLM kombinasyonudur.** Sadece LLM yargıca güvenmeyin.
- **Doğrulanamayan sorularda** (matematik dışı veya SymPy'ın çözemediği) sistem "düşük güven" bayrağı koyar, ipucu seviyesini temkinli tutar ve gerekirse "bunu öğretmenine sor" der.
- **Bütçe/gecikme:** [3], [7b], [8] küçük/ucuz modelle; [4], [6] daha güçlü modelle çalışır (Bölüm 12).
- **Önbellek:** Aynı normalleştirilmiş soru için gizli çözüm (4) önbelleğe alınır (öğrenci verisi içermez, yalnızca soru → çözüm).

### 7.4 Bileşen sorumlulukları

| Modül | Sorumluluk | Ana tablolar |
|---|---|---|
| Auth & Consent | Ebeveyn kaydı, çocuk profili, rıza kayıtları, oturum, rol/yetki | users, guardians, child_profiles, consents |
| Tutoring | Oturum, soru, deneme, ipucu akışı | sessions, problems, attempts, hints |
| Curriculum & Skill | Kazanım, beceri grafı, soru-beceri etiketi | skills, problem_skills |
| Progress & Reporting | Beceri puanı, haftalık rapor, öğretmen ısı haritası | mastery, reports |
| Billing | Abonelik, kota, faturalama webhook'ları | subscriptions, invoices, entitlements |
| Notification | E-posta, push, bildirim tercihleri | notifications, preferences |
| Moderation | Güvenlik olayları, inceleme kuyruğu, hesap kısıtı | moderation_events, flags |
| LLM Gateway | Sağlayıcı soyutlama, retry, timeout, maliyet kaydı, PII maskeleme | llm_calls, prompt_versions |
| Admin | Konsol, eval raporları, içerik yönetimi | audit_log |

### 7.5 Teknoloji yığını seçenekleri

| Katman | Seçenek A | Seçenek B | Seçenek C | Not |
|---|---|---|---|---|
| İstemci (çocuk, ebeveyn, öğretmen) | **Expo / React Native + Web (seçildi) ✅** (TypeScript) | Flutter (D7 ilk karar) | — | Tek kod tabanı: iOS + Android + Web; landing ayrı statik site |
| Backend | **FastAPI (seçildi) ✅** (async, tip güvenli, OpenAPI otomatik) | Django (admin hazır) | — | LLM streaming için async avantajı |
| Veritabanı | PostgreSQL | MySQL | — | Postgres + pgvector tek çatı |
| Önbellek/kuyruk | Redis (+ RQ/Celery/Arq) | RabbitMQ | Cloud queue | Basit başla |
| Arama/Vektör | pgvector | Qdrant | — | MVP'de pgvector yeterli |
| Dosya | S3 uyumlu | Cloud Storage | — | Foto yaşam süresi kısa (retention) |
| Kimlik | Kendi JWT + refresh | Keycloak/Auth0 benzeri | Firebase Auth | Çocuk hesabı özel akış gerektirir |
| Ödeme | iyzico/PayTR (TR) | Stripe | Mağaza içi satın alma (IAP) | ⚠️ Mağaza kuralları: dijital abonelik IAP gerektirebilir. Politikaları doğrula |
| Gözlemlenebilirlik | OpenTelemetry + Grafana | Sentry + hosted | Datadog | Bölüm 13 |
| CI/CD | GitHub Actions | GitLab CI | — | — |
| IaC | Terraform | Pulumi | docker-compose (MVP) | — |
| Matematik doğrulama | SymPy | Wolfram API | — | SymPy ücretsiz, kontrol bizde |
| OCR | Cloud vision API | Tesseract + matematik OCR modeli | LLM vision | Kalite/maliyet/gizlilik dengesi |

### 7.6 Ortamlar

`local` → `dev` → `staging` → `prod`. Prod verisi asla dev/staging'e kopyalanmaz. Çocuk verisi için sentetik test veri seti kullanılır.

### 7.7 Hata ve kesinti stratejisi

- LLM zaman aşımı: 1 yeniden dene, olmazsa ikincil modele düş, olmazsa "şu an yardımcı olamıyorum" + önceden hazırlanmış kendi kendine kontrol listesi.
- Sızıntı kontrolü başarısız (hata): **güvenli taraf** — yanıtı yayınlama, yedek ipucu ver.
- Moderasyon servisi erişilemez: **fail-closed** (çocuk güvenliği için yanıt yok, "Biraz sonra tekrar dene").

---

