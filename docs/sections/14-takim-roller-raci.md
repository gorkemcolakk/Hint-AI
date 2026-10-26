## 14. Takım, Roller, RACI

### 14.1 Rol dağılımı önerisi (6 kişi)

| Kişi | Birincil rol | İkincil sorumluluk |
|---|---|---|
| BM-1 | **Teknik lider / Backend & AI boru hattı** (hint engine, LLM gateway) | Mimari kararlar, kod inceleme |
| BM-2 | **Expo / React Native istemcisi (çocuk + ebeveyn + öğretmen, mobil + web)** | Tasarım sistemi, kullanılabilirlik testi |
| BM-3 | **Eval, veri ve güvenlik mühendisi** (golden set, red-team, SymPy doğrulama, güvenlik) | Veri modeli, PII maskeleme |
| EM-1 | **Ürün & operasyon & birim ekonomisi** (IE) | Süreç tasarımı, KPI, kullanıcı araştırması planı |
| EM-2 | **Finansal model, fiyat, tedarik/kapasite** (IE) | Maliyet optimizasyonu, risk kaydı |
| İŞ-1 | **İş geliştirme, GTM, okul/öğretmen ilişkileri, pitch, hukuk/danışman koordinasyonu** | Müşteri görüşmeleri, marka |

> Rol dağılımı ekip üyelerinin ilgi ve güçlü yanlarına göre ekip toplantısında birlikte netleştirilmelidir (özellikle tasarım sistemi sahibi kim olacak?).
> Tek istemci kod tabanı tek kişiye yüklenirse darboğaz olur; BM-3 ile işi paylaşın.

### 14.2 RACI (özet)

| Faaliyet | BM-1 | BM-2 | BM-3 | EM-1 | EM-2 | İŞ-1 |
|---|---|---|---|---|---|---|
| Mimari ve teknik karar | A/R | C | C | I | I | I |
| Çocuk UI/UX | C | A/R | I | C | I | C |
| Hint engine & eval | R | I | A/R | C | I | I |
| Güvenlik & KVKK uyum | C | I | A/R | C | I | R (hukuk koordinasyonu) |
| Müşteri keşfi / görüşmeler | I | C | I | R | C | A/R |
| Finansal model | I | I | I | C | A/R | C |
| Fiyatlama | I | I | I | C | R | A |
| GTM / pilot | I | I | I | C | C | A/R |
| Pitch / sunum | C | C | C | R | R | A/R |

(R: Yapar, A: Hesap verir, C: Danışılır, I: Bilgilendirilir)

### 14.3 Çalışma biçimi

- Haftalık sprint, 30 dk planlama, 15 dk günlük senkron (asenkron yazılı olabilir), haftalık demo.
- Karar günlüğü (`DECISIONS.md`), varsayım günlüğü (`ASSUMPTIONS.md`).
- Tek gerçek kaynak: bu doküman + issue tracker (GitHub Projects).
- Kod sahipliği (CODEOWNERS), PR şablonu.

---

