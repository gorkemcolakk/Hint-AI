## 2. Canvas Denetimi: Eksikler ve Tutarsızlıklar

### 2.1 Blok bazında denetim

| # | Blok | Güçlü yan | Eksik / Risk | Düzeltme |
|---|------|-----------|--------------|----------|
| 01 | Key Partners | Okul, uzman, platform bağımlılıkları doğru yakalanmış | "Milli Eğitim Bakanlığı" ilk aşamada gerçekçi değil (yıllar süren süreç). Hukuk/KVKK danışmanı, ödeme sağlayıcı, test okulları/öğretmen ambassador'ları yok | Faz 1 ortakları: 2–3 pilot öğretmen, 1 pedagoji danışmanı, 1 hukuk danışmanı (üniversite hukuk kliniği olabilir), ödeme altyapısı. MEB Faz 3'e taşı |
| 02 | Key Activities | Hint engine ve güvenlik doğru | Eval/ölçüm faaliyeti, red-teaming, müşteri keşfi, satış, topluluk yönetimi yok | "AI kalite değerlendirmesi", "kullanıcı araştırması", "okul satış süreci" ekle |
| 03 | Key Resources | Hint sistemi, filtre, veri | **İnsan kaynağı** (ekip), müfredat veri seti (MEB kazanımları), değerlendirme veri seti, marka güveni nasıl kazanılacak belirsiz | "Kazanım-soru veri seti", "eval golden set", "pedagoji danışma kurulu" ekle |
| 04 | Value Prop | "İpucu, cevap değil" net | Ölçülebilir sonuç yok ("%X daha az kopya, %Y daha yüksek bağımsız çözüm oranı"). Rakipten farkı (Khanmigo, Photomath, ChatGPT Study Mode vb.) söylenmemiş. Çocuğun motivasyon problemi (neden cevabı değil ipucunu seçsin?) çözülmemiş | Her segment için tek cümlelik, ölçülebilir değer önerisi (Bölüm 3.1) |
| 05 | Customer Relationships | Ebeveyn paneli, öğretmen paneli iyi | Rozet/streak çocuklar için manipülatif tasarıma kayabilir (etik). Kullanıcı geri bildirim döngüsü ve topluluk yok | "Etik gamification ilkeleri" (Bölüm 5.6) ve "ebeveyn/öğretmen geri bildirim kanalı" |
| 06 | Channels | App Store/Play, okul, ebeveyn toplulukları | 7–12 yaş çocuğa doğrudan pazarlama KVKK/etik açıdan sorunlu. CAC varsayımı yok. Web (PWA) ile mağaza onay riski azaltılmamış | Kanal öncelik sırası + PWA ile hızlı MVP (Bölüm 16) |
| 07 | Customer Segments | Kullanıcı/ödeyici ayrımı çok doğru | 3 kullanıcı grubu + 3 ödeyici = çok geniş. Yaş 7–17 arasında pedagoji, UX ve güvenlik gereksinimleri çok farklı | Tek yaş bandı + tek ders ile başla (Bölüm 3.1) |
| 08 | Cost Structure | LLM, uzman, uyum, pazarlama var | **Ödeme komisyonları, mağaza komisyonu, hukuk, güvenlik testi, sigorta, hosting/izleme, moderasyon insan gücü, muhasebe** eksik. Maliyetler birimlenmemiş | Bölüm 12 |
| 09 | Revenue Streams | Freemium + B2B2C mantıklı | Fiyat yok. "Eğitim yayıncılarıyla ortaklık" gelir değil, ortaklık. "Premium modüller" ürünün çekirdeği değil, dağınık. Okul lisanslama satış döngüsü uzun | Fiyat seçenekleri (Bölüm 3.3), gelir hunisi |

### 2.2 Canvas'ta olmayan ama dersin ve ciddi bir girişimin beklediği öğeler

- **Problem / mevcut alternatifler** (Lean Canvas'ın sol tarafı): öğrenci şu an ne yapıyor? (Kunduz/Photomath'e foto atıyor, ChatGPT'ye soruyor, özel ders, YouTube.)
- **Unfair advantage / savunulabilirlik:** Kopyalanamayan nedir? (Eval veri seti, MEB kazanım eşlemesi, okul ilişkileri, güven markası.)
- **Anahtar metrikler:** Canvas'ta yok (Bölüm 18).
- **Doğrulanmış varsayımlar:** Hiçbir varsayım "doğrulandı" diye işaretli değil. Girişimcilik dersinde en çok puan getiren şey budur (Bölüm 4.3).
- **Finansal projeksiyon:** 12–36 ay gelir/gider tablosu.
- **Etik ve çocuk güvenliği manifestosu:** Güven bu üründe asıl satılan şey.

### 2.3 İç tutarsızlıklar

1. **"Çocuklar ve gençler" ile "sınava hazırlanan öğrenciler"** farklı ürünler isteyebilir (sınav hazırlığı hız ve soru bankası ister, keşif odaklı öğrenme yavaş ve yaratıcı olur).
2. **"Hints, not answers" ile "Fun, game-like learning"** çatışabilir: oyunlaştırma "hızlı bitir" davranışını teşvik ederse ipucu kötüye kullanılır.
3. **Freemium (günlük sınırlı ücretsiz ipucu)** ile **"öğrenci takıldığında yardım"** çatışır: sınır dolunca çocuk takılı kalırsa ürün güvenini kaybeder. Sınır tasarımı kritik (Bölüm 5.5).
4. **Ebeveyn paneli ile gençlerin mahremiyeti:** 13–17 yaş ebeveynin tüm sohbeti görmesini istemez. Panel ne gösterir? (Özet mi, ham sohbet mi?) Bölüm 10.4.
5. **COPPA** (ABD yasası) listelenmiş ama pazar Türkiye ağırlıklı görünüyor. ABD'ye girmeyeceksek ilk aşamada KVKK + Türkiye mevzuatı + mağaza politikaları öncelikli, COPPA/GDPR-K "genişleme" maddesi olmalı.

### 2.4 Ekip kompozisyonuna göre boşluklar

| Eksik yetkinlik | Neden önemli | Çözüm |
|---|---|---|
| Pedagoji uzmanı | İpucu kalitesini ve yaşa uygunluğu ancak o doğrular | Danışman olarak bir öğretmen / eğitim bilimleri akademisyeni |
| Hukuk/KVKK | Çocuk verisi yüksek riskli alan | Üniversite hukuk fakültesi, danışman, hazır şablon + uzman gözden geçirmesi |
| UI/UX (çocuk) | Yaş bandına göre tasarım farklı | Ekipten biri UX'e odaklanmalı (bilgisayar müh. içinden), kullanıcı testi yapılmalı |
| Satış (B2B okul) | Okul satışı ilişki işi | İşletme öğrencisi + öğretmen ağı |
| Veri/ML değerlendirme | Eval olmadan "iyi" iddiası boş | Bilgisayar müh. içinden bir kişi eval sahibi |

---

