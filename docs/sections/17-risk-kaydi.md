## 17. Risk Kaydı

| # | Risk | Olasılık | Etki | Önlem | Sahip |
|---|---|---|---|---|---|
| R1 | İpucu cevabı sızdırır (itibar kaybı, değer önerisi çöker) | Orta | Çok yüksek | Çok katmanlı sızıntı kontrolü, eval CI, hızlı prompt rollback | BM-3 |
| R2 | Çocuk güvenliği olayı (uygunsuz içerik, kriz mesajı yanlış ele alınır) | Düşük-orta | Çok yüksek | Moderasyon, kriz akışı, insan inceleme, hukuk ile politika | BM-3 / İŞ-1 |
| R3 | KVKK/ebeveyn rızası ihlali, yurt dışına aktarım uyumsuzluğu | Orta | Yüksek | PII maskeleme, rıza modülü, hukuk görüşü, veri işleme envanteri | İŞ-1 / BM-3 |
| R4 | LLM maliyeti geliri aşar | Orta | Yüksek | Bütçe tavanı, model yönlendirme, önbellek, fiyat testi | EM-2 |
| R5 | Çocuk ipucu mekanizmasından sıkılır, terk eder ("ipucu bıkkınlığı") | Yüksek | Yüksek | Kullanılabilirlik testi, escalation ayarı, duygu desteği, çözüm örneği L4 | BM-2 |
| R6 | Büyük oyuncular (ChatGPT/Gemini öğrenme modları, Khanmigo) özelliği ücretsiz sunar | Yüksek | Yüksek | Müfredat uyumu, ebeveyn/öğretmen paneli, güven ve yerel pazar, B2B | İŞ-1 |
| R7 | Ebeveyn ödeme istemiyor | Orta | Yüksek | Erken fiyat testi, öğretmen kanalı, B2B alternatif | EM-1 |
| R8 | Okul satış döngüsü çok uzun | Yüksek | Orta | B2C ile paralel ilerle, öğretmen pilotları | İŞ-1 |
| R9 | Mağaza onayı/politika engeli (Kids/Families, IAP kuralları) | Orta | Orta | PWA yolu, politika ön kontrolü | BM-2 |
| R10 | Yanlış/halüsinasyon ipucu çocuğu yanıltır | Orta | Yüksek | SymPy doğrulama, düşük güven bayrağı, kapsam sınırı (matematik) | BM-1 |
| R11 | Ekip kapasitesi/ders yükü (6 öğrenci, dönem yoğunluğu) | Yüksek | Orta | Kapsam disiplini, MVP kesintisi, net öncelik | Tümü |
| R12 | Sağlayıcı bağımlılığı/fiyat/politika değişikliği | Orta | Orta | LLM Gateway soyutlaması, yedek sağlayıcı | BM-1 |
| R13 | Veri ihlali | Düşük | Çok yüksek | Şifreleme, erişim kontrolü, minimizasyon, olay müdahale planı | BM-3 |
| R14 | İntihal/akademik dürüstlük algısı (öğretmenler ürüne güvenmez) | Orta | Orta | Şeffaf rapor, "çözüm görüldü" bildirimi, öğretmen paneli | İŞ-1 |
| R15 | Telif (içerik, görsel, marka) | Düşük | Orta | Kendi içerik/lisans, marka taraması | İŞ-1 |
| R16 | Web'de erişilebilirlik ve ilk yükleme (D7-r ile azaltıldı: react-native-web DOM üretir) | Düşük | Orta | Landing ayrı site, erişilebilirlik etiketleri + ekran okuyucu testi, web bundle boyutu takibi | BM-2 |
| R17 | Tek frontend geliştirici darboğazı (tek istemci kod tabanı) | Orta | Orta | İş paylaşımı, ortak bileşen kütüphanesi | BM-2 |
| R18 | Ekibin React / TypeScript'e yeni olması (öğrenme eğrisi, M6 gecikmesi) | Orta | Orta | M1.5'te küçük iskeletle başla, kavramları Flutter karşılıklarıyla öğren, her istemci PR'ında kod incelemesi | BM-2 |

---

