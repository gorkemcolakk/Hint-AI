## 12. Maliyet ve Birim Ekonomisi

### 12.1 Maliyet kalemleri (Canvas'a eklenecek tam liste)

**Değişken (kullanıcı başına):**
- LLM çağrıları (sınıflandırma, çözüm, ipucu, yargıç, güvenlik)
- OCR/vision
- Altyapı (hesaplama, DB, depolama, bant genişliği)
- Ödeme komisyonu (%), mağaza komisyonu (⚠️ DOĞRULA güncel oranlar/programlar)
- Müşteri desteği (kullanıcı başına zaman)
- E-posta/SMS/push

**Sabit/dönemsel:**
- Hukuk ve KVKK danışmanlığı, VERBİS (gerekiyorsa)
- Güvenlik testi/pentest
- Pedagoji danışmanı
- İçerik/kazanım veri seti hazırlama
- Marka, tasarım, alan adı, geliştirici hesapları (Apple/Google)
- İzleme/log araçları
- Muhasebe, şirket kuruluşu (gerçek girişimde)
- Sigorta (siber, mesleki sorumluluk) — gerçek girişim aşamasında
- Moderasyon insan inceleme süresi

### 12.2 LLM maliyet modeli (doldurulacak formül)

```
Soru başına LLM maliyeti =
    Σ_(adım ∈ {sınıflandır, çöz, ipucu×k, yargıç×k, güvenlik×k})
        (girdi_token × girdi_fiyatı + çıktı_token × çıktı_fiyatı)

Kullanıcı başı aylık LLM maliyeti =
    (günlük soru sayısı) × (soru başı ortalama ipucu sayısı) × (ipucu başı maliyet) × (aktif gün)
    + (soru başı gizli çözüm maliyeti × soru sayısı × (1 - önbellek isabet oranı))
```

Kontrol değişkenleri: model yönlendirme (ucuz model ağırlığı), önbellek isabeti, bağlam kısaltma, ipucu başına çıktı üst sınırı, günlük bütçe limiti.
**Fiyatlar güncel sağlayıcı fiyat listesinden alınır (⚠️ DOĞRULA).** Rakam uydurmayın; önce **10 gerçekçi oturumu** ölçerek token ortalamalarını çıkarın.

### 12.3 Birim ekonomisi şablonu (Excel/Sheets sayfaları)

| Sayfa | İçerik |
|---|---|
| `Varsayımlar` | Fiyat, dönüşüm oranı, churn, CAC, soru/gün, ipucu/soru, token ortalamaları, model fiyatları, komisyon oranları |
| `Birim_Ekonomi` | ARPU, değişken maliyet/kullanıcı, brüt marj, LTV = ARPU × brüt marj / aylık churn, CAC, geri ödeme süresi |
| `Senaryolar` | Kötümser/baz/iyimser (üçü yan yana) |
| `Gelir_Projeksiyonu` | 24–36 ay: ücretsiz→ücretli dönüşüm hunisi, okul lisansları |
| `Gider_Projeksiyonu` | Sabit + değişken, ekip maaşları (gerçek girişimde) |
| `Başabaş` | Başabaş kullanıcı/okul sayısı |
| `Duyarlılık` | LLM fiyatı ±, churn ±, dönüşüm ± ile marj değişimi |

Hedef göstergeler (girişimcilik sezgisi, ⚠️ doğrulayın): LTV/CAC ≥ 3, CAC geri ödeme ≤ 12 ay, brüt marj SaaS benzeri yüksek hedef; ücretsiz kullanıcı maliyeti toplam gelirin kabul edilebilir bir yüzdesi (ekip belirler).

### 12.4 Maliyet kontrol mekanizmaları (mimaride)

- Kullanıcı/gün token bütçesi, global kesici.
- Model yönlendirme: kolay işler küçük modele.
- Soru bazlı çözüm önbelleği.
- Çıktı uzunluğu üst sınırı (çocuk için zaten kısa olmalı).
- Ücretsiz kullanıcı için daha sıkı bütçe; kötüye kullanım tespiti (bot, çoklu hesap).

---

