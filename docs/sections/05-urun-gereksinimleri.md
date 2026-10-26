## 5. Ürün Gereksinimleri

### 5.1 Personalar

| Persona | Tanım | Temel ihtiyaç | Başarı |
|---|---|---|---|
| **Deniz (11, 6. sınıf)** | Çocuk kullanıcı | Takılınca utanmadan yardım, oyun hissi | Soruyu kendi çözer, gurur duyar |
| **Can (15, 9. sınıf)** | Genç | Hızlı, saygılı, mahremiyet | Zaman kaybetmeden anlar, ebeveyn her şeyi görmez |
| **Elif Hanım (40, anne)** | Ödeyici | Çocuğun öğrendiğinden emin olmak, kontrol ama baskısız | Haftalık özette gerçek ilerleme görür |
| **Murat Öğretmen (35)** | Sınıf öğretmeni | Ödev dürüstlüğü, sınıf teşhisi | Hangi kazanımda sınıf zorlanıyor görür |
| **Okul müdürü / satın alan** | B2B karar verici | Güvenlik, KVKK, maliyet | Sözleşme ve uyum belgesi |

### 5.2 Kullanıcı hikâyeleri (MVP çekirdeği)

**Çocuk**
- Soruyu metin olarak yazarım veya fotoğrafını çekerim.
- Bot önce soruyu anladığımı kontrol eder.
- "Takıldım" dediğimde bir sonraki ipucu seviyesine geçer.
- Her ipucu bir soru veya küçük adımdır, cevabı vermez.
- Çözümümü yazarım, bot doğru/yanlış söyler ve nedenini ipucuyla gösterir.
- Başardığımda küçük kutlama alırım (aşırı değil).

**Ebeveyn**
- Çocuğum için hesap oluştururum, açık rıza veririm.
- Günlük ipucu limitini ve "çözümü göster" politikasını ayarlarım.
- Haftalık rapor alırım: konu, kaç soru, kaç ipucuyla, bağımsızlık oranı.
- Verilerimi indirir/silerim.

**Öğretmen**
- Sınıf oluştururum, davet kodu veririm.
- Sınıf bazlı kazanım zorluk haritası görürüm.
- Öğrenci bazlı ham sohbeti değil, özet ve ilerleme görürüm (gizlilik).

**Admin/Moderatör**
- Güvenlik filtresine takılan oturumları incelerim, hesabı kısıtlarım.
- Prompt sürümlerini ve eval sonuçlarını görürüm.

### 5.3 MVP kapsamı ve kapsam dışı

| MVP içinde | MVP dışında (sonra) |
|---|---|
| Matematik, seçilen yaş bandı, metin giriş | Çoklu ders |
| Fotoğraftan soru (OCR) — **kapsam sıkışırsa Faz 2** | Sesli etkileşim |
| İpucu merdiveni L0–L4 | Tam kişiselleştirilmiş müfredat yolu |
| Ebeveyn hesabı + çocuk profili + onay akışı | Okul SSO, MEBBİS entegrasyonu |
| Basit streak + rozet (etik sınırlı) | Sosyal/arkadaş özellikleri (güvenlik riski) |
| Haftalık ebeveyn raporu (e-posta) | Gelişmiş analitik panosu |
| Öğretmen paneli: sınıf + davet kodu + kazanım ısı haritası (minimal) | Tam LMS |
| Abonelik (tek plan) | Çoklu plan, kurumsal faturalama |
| TR dili | Çok dilli |

### 5.4 Fonksiyonel olmayan gereksinimler

| Alan | Hedef (öneri) |
|---|---|
| Performans | İpucu ilk token < 2 sn, tam yanıt p95 < 6 sn |
| Erişilebilirlik | WCAG 2.1 AA, disleksi dostu yazı tipi seçeneği, ekran okuyucu uyumu. react-native-web DOM üretir; erişilebilirlik etiketleri (`accessibilityLabel`, `role`) zorunlu, web ve mobilde ekran okuyucu ile test edilir. |
| Kullanılabilirlik | 7–12 yaş için büyük dokunma alanı, minimal metin, okuma seviyesine uygun dil |
| Güvenilirlik | %99.5 uptime (MVP), LLM kesintisinde zarif düşüş ("şu an ipucu veremiyorum, şunu deneyebilirsin") |
| Çevrimdışı | Hafif: son oturum önbelleği; tam offline kapsam dışı |
| Güvenlik | Bölüm 10 |
| Ölçeklenme | MVP: 1.000 eşzamanlı oturum tasarım hedefi; yük testi ile doğrula |
| Bakım | Prompt ve model versiyonlama, geri alınabilir yayınlar |

### 5.5 Freemium sınırı tasarımı

Sorun: günlük limit dolunca çocuk takılı kalır.
Çözüm seçenekleri:
1. **Limit "ipucu" değil "yeni soru" sayısıdır.** Başlanmış soru bitirilir.
2. Limit dolunca **kendi kendine kontrol listesi** ve "yarın devam" kaydı gösterilir (sıfır maliyetli yardım).
3. Ebeveyne "bugün bir ek soru ver" tek tık izni.

### 5.6 Etik gamification ilkeleri

- Streak kaybı için ceza/üzüntü mesajı yok ("seri koptu" yerine "yeniden başlayalım").
- Rozetler **bağımsız çözüm** ve **azalan ipucu** için verilir, hız için değil.
- Rastgele ödül (loot box) yok. Sosyal karşılaştırma/sıralama çocuk için yok.
- Bildirim sınırı: günde en fazla 1, akşam 20:00'den sonra yok, ebeveyn kapatabilir.
- Dark pattern yasağı: "kaçırma korkusu" (FOMO) mesajları yok.

### 5.7 UX ilkeleri

- Yaş bandına göre iki tema: **Keşif (7–12)** ve **Odak (13–17)**.
- Her ekranda tek ana eylem.
- Bot kişiliği: sabırlı, meraklı, yargılamayan; yanlışa "yanlış" yerine "bir de şuna bakalım".
- Boş durumlar, hata durumları, yükleniyor durumları tasarlanır (kütüphane: Figma bileşenleri).
- Ebeveyn paneli ve öğretmen paneli çocuk uygulamasından görsel olarak ayrışır (aynı Expo istemcisi içinde ayrı tema ve route grubu olarak).

---

