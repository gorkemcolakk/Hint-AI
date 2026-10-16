## 6. Pedagoji Tasarımı: İpucu Merdiveni

### 6.1 İlkeler (öğrenme bilimi dayanakları — pedagoji danışmanı ile doğrulayın)

- **Üretken mücadele (productive struggle):** Öğrenci biraz zorlanmalı ama pes etmemeli.
- **Sokratik sorgulama:** Cevabı soruyla yönlendir.
- **İskele ve sönümleme (scaffolding & fading):** Destek zamanla azalır.
- **Metabilişsel yönlendirme:** "Ne biliyorum? Ne isteniyor? Plan ne?"
- **Aralıklı tekrar ve benzer soru:** Aynı beceri farklı sayılarla tekrar test edilir.

### 6.2 İpucu seviyeleri

| Seviye | Ad | Ne yapar | Örnek (soru: "3x + 5 = 20, x kaçtır?") | Cevabı verir mi |
|---|---|---|---|---|
| **L0** | Anlama kontrolü | Soruyu öğrenciye anlattırır | "Bu denklemde bilmediğimiz şey ne? Neyi bulmaya çalışıyoruz?" | Hayır |
| **L1** | Kavram yönü | Hangi kavram/konu ilgili | "Eşitliğin iki tarafında yapılan işlem dengeyi korur. Bunu nasıl kullanabiliriz?" | Hayır |
| **L2** | Strateji | Yöntem ipucu | "x'i yalnız bırakmak istiyoruz. Önce hangi sayıdan kurtulmak daha kolay olur?" | Hayır |
| **L3** | Kısmi adım | İlk adımı birlikte yapar, sonrasını öğrenciye bırakır | "İki tarafından 5 çıkarırsak sol tarafta ne kalır? Sağ tarafı sen hesapla." | Hayır (ara değer verilebilir, son sonuç verilmez) |
| **L4** | Benzer çözümlü örnek | Farklı sayılarla tam çözümlü örnek | "2x + 3 = 11 örneğine bakalım, adımları gör, sonra senin sorunda dene." | Hayır (asıl soru çözülmez) |
| **L5** | Çözüm gösterimi | Politika kilidi açıksa tam çözüm | — | Evet, kayıt + bildirim |

### 6.3 Yükselme (escalation) kuralları

Bir sonraki seviyeye geçiş tetikleyicileri:
- Öğrenci "bilmiyorum/takıldım" yazdı.
- 2 başarısız deneme yaptı.
- Belirli süre etkileşimsiz kaldı (örn. 90 sn) ve "yardım ister misin?" sorusuna evet dedi.
- Duygu sinyali: "çok zor", "yapamıyorum", "sıkıldım" (frustrasyon). Bu durumda önce duygusal destek + bir seviye yükselt.

Düşme (de-escalation): öğrenci doğru adım atarsa bir sonraki ipucu seviyesi sıfırlanır (L0/L1).

### 6.4 Öğrenci modeli

| Seçenek | Karmaşıklık | Artı | Eksi |
|---|---|---|---|
| Basit sayaç (beceri başına doğru/yanlış, ipucu seviyesi ortalaması) | Düşük | MVP'de yeterli, açıklanabilir | Kaba |
| Elo/IRT benzeri beceri puanı | Orta | Zorluk ayarı | Veri gerekir |
| Bayesian Knowledge Tracing (BKT) | Orta-yüksek | Akademik temel | Parametre kalibrasyonu |
| Derin bilgi izleme (DKT/transformer) | Yüksek | — | MVP için gereksiz |

> MVP: Basit sayaç + her beceri için `independence_score = çözülen_soru_ipucu_seviyesi_ortalaması`. Faz 2'de Elo.

### 6.5 Beceri taksonomisi (kazanım eşlemesi)

- MEB kazanımları (⚠️ DOĞRULA güncel müfredat kodları) → `skills` tablosu (`code`, `grade`, `subject`, `title_tr`, `prerequisites[]`).
- Her soru bir veya birden fazla beceriye etiketlenir (başlangıçta manuel/yarı otomatik, LLM önerir, insan onaylar).
- Önkoşul grafı: takılma tespitinde "önceki konuda eksik mi?" önerisi.

### 6.6 Yanlış kavram (misconception) kütüphanesi

Matematikte yaygın hatalar (ör. `(a+b)² = a²+b²`, işaret hatası, kesirde paydaları toplama) için kalıplar tutulur. Öğrencinin yanlış cevabı bir kalıpla eşleşirse ipucu doğrudan o yanlış kavramı hedefler. Bu liste ürünün **savunulabilir veri varlığı**dır, öğretmenlerle birlikte büyütün.

### 6.7 Yaşa göre dil

| Yaş bandı | Ton | Cümle uzunluğu | Örnek/metafor | Emoji |
|---|---|---|---|---|
| 7–10 | Oyunsu, sıcak | Çok kısa | Günlük nesneler | Az |
| 11–13 | Arkadaşça | Kısa-orta | Oyun, spor | Çok az |
| 14–17 | Saygılı, doğrudan | Orta | Gerçek hayat, sınav bağlamı | Yok/çok az |

---

