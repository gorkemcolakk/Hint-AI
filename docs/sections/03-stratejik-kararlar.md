## 3. Stratejik Kararlar (Seçenek Tabloları)

> Bu bölümde her kararın seçenekleri yan yana verildi. "Hangisi?" sorusuna ekip kendi koşullarına göre karar verir. Kararlar `DECISIONS.md` içine yazılır.

### 3.1 Hedef segment (beachhead)

| Kriter | A) 5–8. sınıf, Matematik, ebeveyn ödeyici | B) 9–12. sınıf, Matematik/Fizik, bireysel genç ödeyici | C) 1–4. sınıf, temel okuryazarlık/matematik, ebeveyn | D) Okul/dershane (B2B), tek öğretmen pilotu |
|---|---|---|---|---|
| Doğrulanabilirlik (SymPy ile) | Yüksek | Orta-yüksek (Fizik zor) | Yüksek | Yüksek |
| Çocuk güvenliği yükü | Orta | Orta (13+ mahremiyet) | **Çok yüksek** (7–12 yaş) | Orta |
| Ödeme istekliliği | Yüksek (LGS motivasyonu) ⚠️ DOĞRULA | Orta (YKS için başka güçlü rakipler) | Orta | Düşük-orta, süreç uzun |
| Rekabet yoğunluğu | Yüksek | Çok yüksek | Orta | Orta |
| Kanal erişimi | Ebeveyn grupları, öğretmenler | Sosyal medya (regülasyon riski) | Okul-aile birliği | Doğrudan öğretmen |
| MVP süresi | Kısa | Orta | Kısa ama güvenlik pahalı | Kısa (tek sınıf) |
| Ders puanı (doğrulama kolaylığı) | Çok iyi | İyi | Orta | Çok iyi (somut pilot) |

**Karar kuralı:**
- Zamanınız dar ve güvenlik/hukuk yükünü azaltmak istiyorsanız → **A** (5–8. sınıf matematik) ve **D** (pilot öğretmen) kombinasyonu.
- Gelir hızı öncelikse → B, ama rekabet ve YKS içeriği yükü artar.
- C en ağır uyum yükünü taşır, MVP için önerilmez.

### 3.2 Ürün kapsamı (ilk ders)

| Ders | Doğrulanabilirlik | İçerik üretimi | Risk | Not |
|---|---|---|---|---|
| Matematik | SymPy ile kesin | Kolay (şablon + MEB kazanım) | Düşük | MVP için en güvenli |
| Fen Bilimleri | Kısmi | Orta | Orta (yanlış bilgi) | Faz 2 |
| Türkçe (paragraf) | Zor (özneldir) | Orta | Orta | Faz 2, rubric gerekir |
| İngilizce | Orta | Orta | Düşük | Faz 3 |

### 3.3 Fiyatlandırma modeli

| Model | Artı | Eksi | Ne zaman |
|---|---|---|---|
| Freemium (günlük N ipucu) + aile aboneliği | Düşük giriş bariyeri, viral | LLM maliyeti ücretsiz kullanıcıda yanar | Ebeveyn B2C |
| Ücretsiz deneme (7–14 gün) → abonelik | Maliyet kontrollü | Çocuk verisi ile deneme dönüşümü etik hassasiyeti | Gelir hızı öncelikse |
| Okul/sınıf lisansı (öğrenci başı yıllık) | Öngörülebilir gelir, düşük CAC/öğrenci | Uzun satış döngüsü, ihale/bütçe | Pilot sonrası |
| Hibrit: öğretmen ücretsiz, öğrenci/aile ücretli | Öğretmen dağıtım kanalı olur | Gelir gecikmeli | **Dağıtım için önerilen kombinasyon seçeneği** |

Fiyat noktaları: `⚠️ DOĞRULA` — en az 15 ebeveyn görüşmesinde "Van Westendorp" fiyat duyarlılığı sorularıyla belirleyin (çok ucuz / ucuz / pahalı / çok pahalı). Rakip fiyatlarını güncel olarak tabloya ekleyin (Bölüm 4.2).

### 3.4 İpucu politikası: "Çözümü göster" butonu olacak mı?

| Seçenek | Artı | Eksi |
|---|---|---|
| 1. Hiç olmasın | Değer önerisi saf | Çocuk bırakıp gider, ChatGPT'ye döner |
| 2. N deneme + bekleme süresi sonrası açılır, ebeveyne/öğretmene "çözüm görüldü" bildirimi | Dengeli, şeffaf | Tasarım karmaşık |
| 3. Sadece ebeveyn/öğretmen açabilir | Kontrol onlarda | Gençlerde sürtünme |
| 4. Çözüm "benzer örnek" olarak gösterilir (farklı sayılarla), asıl soru çözülmez | Pedagojik olarak güçlü | Bazı sorularda benzer örnek üretmek zor |

> **Varsayılan taslak (ekip onaylayana kadar):** Seçenek 2 + 4 birleşimi, politika `child_profile.solution_policy` alanında tutulur ve ebeveyn/öğretmen değiştirir.

### 3.5 LLM sağlayıcı stratejisi

| Seçenek | Artı | Eksi | Not |
|---|---|---|---|
| Tek bulut LLM API (örn. Claude, GPT, Gemini) | En hızlı MVP, yüksek kalite | Yurt dışına veri aktarımı (KVKK), maliyet, bağımlılık | PII maskeleme zorunlu |
| Çoklu sağlayıcı + yönlendirme (router) | Maliyet/kalite optimizasyonu, yedeklilik | Karmaşıklık, prompt'ları her model için test | Faz 2 |
| Açık kaynak model, kendi barındırma (GPU) | Veri ülkede kalabilir, birim maliyet düşebilir | GPU maliyeti, kalite, operasyon yükü | Okul B2B talebi olursa |
| Hibrit: sınıflandırma/moderasyon küçük model, hint üretimi büyük model | Maliyet düşer | Çok bileşen | **Mimari bunu desteklemeli (Bölüm 7)** |

Mimari kural: **LLM çağrıları tek bir `llm-gateway` modülünden geçer.** Sağlayıcı değişimi tek yerde yapılır.

### 3.6 Barındırma

| Seçenek | Artı | Eksi |
|---|---|---|
| Büyük bulut (AWS/GCP/Azure), AB/TR'ye yakın bölge | Olgun servisler, kredi/öğrenci programları | Maliyet, karmaşıklık |
| Ucuz VPS/bulut (Hetzner vb.) | Düşük maliyet | Güvenlik/yedekleme sorumluluğu sizde |
| Türkiye'deki veri merkezi sağlayıcıları | Veri yerelliği hikâyesi | Servis çeşitliliği daha az |
| PaaS (Render/Railway/Fly vb.) | Çok hızlı | Ölçeklenince pahalı, bölge sınırları |

### 3.7 Mobil/Web yaklaşımı

| Seçenek | Artı | Eksi |
|---|---|---|
| Flutter (iOS+Android+Web tek kod) | Ekipte bilgi var, tek kod tabanı | Web SEO zayıf, mağaza onayı |
| PWA (web önce) | Mağaza onayı yok, hızlı iterasyon, okullarda tarayıcı ile kullanım | Push/kamera sınırlamaları |
| Flutter mobil + ayrı web (ebeveyn/öğretmen paneli için React/Next.js) | Panel ihtiyaçlarına uygun | İki tech stack |

Karar (D7): Flutter, tek kod tabanından iOS + Android + Web. Landing page ayrı, basit bir statik site.

---

