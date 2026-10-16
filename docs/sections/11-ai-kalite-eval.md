## 11. AI Kalite Güvencesi ve Değerlendirme (Eval)

> "Cevap vermiyoruz" iddiası ölçülmezse pazarlama sloganıdır. Eval sistemi ürünün güven kanıtıdır.

### 11.1 Değerlendirme boyutları ve hedefler (öneri hedefler, ekip kalibre eder)

| Boyut | Metrik | Hedef (ilk) |
|---|---|---|
| Cevap sızıntısı | L0–L3'te nihai cevabın açığa çıkma oranı | < %1 (golden set üzerinde) |
| Doğruluk | Gizli çözümün doğrulanmış (SymPy) olma oranı | ≥ %98 (matematik, MVP kapsamı) |
| İpucu yararlılığı | Öğretmen rubric ortalaması (1–5) | ≥ 4.0 |
| Pedagojik uygunluk | Seviyeye uygunluk (L2 gerçekten strateji mi?) | ≥ %90 |
| Yaş uygunluğu | Ton/dil uyumu | ≥ %95 |
| Güvenlik | Red-team senaryolarında doğru ele alma | ≥ %99 (kritik kategoriler %100 hedef) |
| Prompt injection direnci | "Cevabı ver" saldırı setinde başarısız saldırı oranı | ≥ %98 |
| Gecikme | p95 | Bölüm 5.4 |
| Maliyet | Çözülen soru başına maliyet | Bölüm 12 hedefi |
| Türkçe dil kalitesi | Dil bilgisi/doğallık, insan puanı | ≥ 4.0 |

### 11.2 Veri setleri

- **Golden set:** Sınıf/kazanım dağılımlı en az 200–500 soru (MVP), doğru çözüm ve beklenen ipucu özellikleriyle. Öğretmenlerle birlikte üretin.
- **Adversarial set:** "Cevabı söyle", "sistemi unut", rol yapma, çok adımlı manipülasyon, Türkçe argo, imla hatalı girdiler.
- **Güvenlik seti:** Kendine zarar, uygunsuz içerik, kişisel bilgi paylaşma, zorbalık (**etik ve güvenli üretim**, hassas içerik ekibe zarar vermeyecek şekilde yönetilir).
- **Gerçek kullanıcı örnekleri:** Rıza ile, anonimleştirilmiş, sürekli iyileştirme için.

### 11.3 Eval süreci

1. Her prompt/model değişikliği → otomatik eval (CI'da) → regresyon varsa birleştirme engellenir.
2. LLM-yargıç kullanılıyorsa **insan örnekleme ile kalibre edilir** (yargıç yanlılığı riski).
3. Öğretmen/pedagog aylık örnek inceleme (en az 50 etkileşim).
4. A/B testi: yeni ipucu stratejisi küçük trafikte, bağımsız çözüm oranı ve ipucu memnuniyeti ile karşılaştırılır.
5. Eval raporları `eval_reports` ile prompt sürümüne bağlanır.

### 11.4 Pedagojik etki deneyi (ders için güçlü kanıt)

- Küçük örneklem (ör. 20–30 öğrenci, velilerin izniyle) iki gruba bölünür: A) cevap veren asistan, B) Hint.ai.
- Aynı konu, ertesi gün (veya birkaç gün sonra) **benzer** sorularla bağımsız test.
- Sonuç, sınırlılıklarıyla (küçük örneklem, bilimsel genelleme yok) dürüstçe sunulur. Bu, "kanıta dayalı girişim" puanı getirir.

### 11.5 Model ve prompt yönetimi

- Prompt'lar kodda değil `prompts/` dizininde sürümlü dosyalar, değişiklik PR ile.
- Model yükseltmesi → tam eval olmadan prod'a çıkmaz.
- Sağlayıcı sürüm pinleme (alias değil sürüm adı kullan), deprecation takvimi izlenir.

---

