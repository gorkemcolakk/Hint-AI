## 10. Güvenlik, Çocuk Güvenliği ve Yasal Uyum

> ⚠️ Bu bölüm hukuki tavsiye değildir. Bir hukuk danışmanıyla doğrulayın. Yasa ve eşik değerleri değişebilir.

### 10.1 Yasal/regülasyon çerçevesi

| Konu | Kapsam | Mimari etkisi |
|---|---|---|
| **KVKK (6698)** | Çocuk verisi, açık rıza, aydınlatma metni, veri sorumlusu yükümlülükleri, VERBİS kaydı eşikleri (⚠️ DOĞRULA), yurt dışına aktarım kuralları (LLM API'leri bu kapsama girebilir, ⚠️ DOĞRULA güncel mevzuat) | Rıza modülü, PII maskeleme, saklama politikası, silme akışı, veri işleme envanteri |
| **Çocuk verisi hassasiyeti** | Reşit olmayan için ebeveyn rızası, minimizasyon | Çocuktan e-posta/telefon toplamama, takma ad, doğum yılı |
| **GDPR / GDPR-K** | AB'ye açılırsa | Faz 3; mimariyi ona uygun tut (silme, taşınabilirlik) |
| **COPPA (ABD)** | ABD'li <13 hizmeti verilirse | Başlangıçta ABD'yi hedefleme; mağaza ülke kısıtı |
| **EU AI Act** | Eğitim alanındaki bazı AI sistemleri yüksek riskli sayılabilir (⚠️ DOĞRULA kapsam) | AB'ye girilirse risk sınıflandırması |
| **Apple App Store "Kids" / Google Play "Families" politikaları** | Reklam/izleme/analitik kısıtları, ebeveyn kapısı (parental gate) | Üçüncü taraf SDK'ları sınırla, parental gate |
| **E-ticaret/Mesafeli satış, tüketici hukuku** | Abonelik, cayma, iptal | Faturalama akışı ve metinler |
| **Fikri mülkiyet** | MEB/yayıncı içeriği telif | Kendi içerik üretin veya lisanslayın |

### 10.2 Çocuk güvenliği tasarımı

| Tehdit | Önlem |
|---|---|
| Kişisel bilgi paylaşımı (adres, telefon, okul) | Girdide tespit → maskele → "bunları paylaşmamalıyız" nazik uyarısı |
| Kendine zarar/intihar, istismar ifadeleri | Sınıflandırıcı → ipucu akışını durdur → sakin, destekleyici mesaj + **yetişkine ulaşma yönlendirmesi** (ülke acil hatları: ⚠️ DOĞRULA, ör. 112, ALO 183 sosyal destek) + ebeveyne/moderatöre bildirim politikası (hukuk ile belirle) |
| Uygunsuz içerik (cinsel, şiddet) | Girdi/çıktı filtreleri, bloklama, kayıt |
| Yabancılarla temas / grooming | Sosyal özellik **yok**; sohbet yalnızca bot ile |
| Siber zorbalık (ders dışı konuşma) | Konu dışı yönlendirme ("Bu konuda sana yardım edemem, güvendiğin bir yetişkinle konuş") |
| Prompt injection / jailbreak ("cevabı ver", "sistem promptunu göster") | Sistem prompt'u güçlü, girdi tespiti, çıktı kontrolü, **sızıntı kontrolü bağımsız katman** |
| Ödev kopyalama kötüye kullanımı | Sızıntı kontrolü + "çözümü göster" kaydı + öğretmene bildirim |
| Aşırı bağımlılık/duygusal bağ | Oturum süresi nazik hatırlatma, bot kendisini yapay zekâ olarak açıkça tanıtır, insan ilişkisinin yerine geçmez |
| Yanlış/halüsinasyon bilgi | SymPy doğrulama, düşük güven bayrağı, "emin değilim, öğretmenine sor" |
| Zararlı yönlendirme (tehlikeli deney vb.) | Fen modülünde güvenlik kuralları |

### 10.3 Uygulama güvenliği (AppSec)

- **Kimlik:** parola hash (argon2/bcrypt), e-posta doğrulama, MFA (ebeveyn/öğretmen/admin için isteğe bağlı, admin için zorunlu), brute-force koruması.
- **Token saklama:** mobilde expo-secure-store (Keychain/Keystore), webde httpOnly cookie. Çocuk modunda üçüncü taraf SDK yok, parental gate uygulanır.
- **Yetkilendirme:** RBAC + nesne düzeyi kontrol (IDOR önleme). Öğretmen yalnızca ebeveyn onaylı öğrencilerin verisini görür.
- **Aktarım ve depolama:** TLS 1.2+, veritabanı disk şifrelemesi, hassas alanlarda uygulama düzeyi şifreleme (`hidden_solution`, ham foto).
- **Sır yönetimi:** Ortam değişkeni değil sır yöneticisi, repoya sır koymama (pre-commit secret scan).
- **Bağımlılıklar:** Dependabot/SCA, imzalı imajlar, minimal imaj.
- **OWASP Top 10 + OWASP LLM Top 10:** prompt injection, güvensiz çıktı işleme, aşırı yetki, model DoS (maliyet saldırısı) için kontrol listesi.
- **Rate limit ve bütçe tavanı:** Kullanıcı/gün token limiti, global günlük harcama alarmı ve kesici (circuit breaker).
- **Yedekleme:** Günlük otomatik, geri yükleme testi aylık.
- **Olay müdahale planı:** Veri ihlali bildirim süreci (KVKK bildirim yükümlülükleri ⚠️ DOĞRULA), sorumlu kişi, iletişim şablonu.
- **Penetrasyon testi:** Yayın öncesi en az bir bağımsız test/gözden geçirme.

### 10.4 Gizlilik tasarımı (privacy by design)

- **Veri minimizasyonu:** Takma ad, doğum yılı, sınıf.
- **Amaç sınırlaması:** Sohbet verisi model eğitimi için **kullanılmaz** (sağlayıcı sözleşmesinde eğitime kapalı/zero-retention seçeneği ⚠️ DOĞRULA).
- **LLM'e giden veri:** Yalnızca maskeli soru metni + gerekli bağlam. Ad, okul, kimlik tipi bilgi gitmez.
- **Gençlerde (14+) gizlilik:** Ebeveyn varsayılan olarak **özet** görür (konu, süre, bağımsızlık oranı, güvenlik uyarıları). Tam transkript ayrı, açık ve gence bildirilen bir ayardır.
- **Şeffaflık:** Çocuğa uygun dilde "Ben bir yapay zekâyım, yanlış yapabilirim" bildirimi.
- **Haklar:** Ebeveyn erişim, düzeltme, silme, taşıma (`/export`, `DELETE`).
- **DPIA/etki değerlendirmesi:** Çocuk verisi için yazılı gizlilik etki değerlendirmesi taslağı hazırla.

### 10.5 Rıza akışı (özet)

1. Ebeveyn hesap açar → e-posta doğrular.
2. Aydınlatma metni + amaç bazlı ayrı onay kutuları (hizmet, LLM işleme, foto işleme, analitik). **Hizmet için gerekmeyen onaylar önceden işaretli olmaz.**
3. Rıza sürüm numarası ve kanıt (zaman, IP hash) kaydedilir.
4. Çocuk cihazına (mobil) eşleştirme kodu ile, webde ebeveynin ürettiği tek kullanımlık, kısa süreli bağlantı veya kod ile bağlanır. Çocuk e-posta veya şifre girmez.
5. Rıza geri çekilince ilgili işleme durur ve veri silme/anonimleştirme tetiklenir.
6. Ebeveyn doğrulama yöntemi: e-posta + (isteğe bağlı) küçük kart doğrulaması/başka güvenli yöntem. ⚠️ DOĞRULA yasal yeterlilik.

---

