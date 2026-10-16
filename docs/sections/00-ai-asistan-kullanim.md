## 0. AI Asistanı İçin Kullanım Talimatı

Bu bölüm bir AI kodlama asistanına verilirse bağlam olarak şunu bilmelidir:

**Proje:** Hint.ai, 7–17 yaş arası çocuk ve gençler için cevabı doğrudan vermeyen, adım adım ipucu veren bir AI öğrenme arkadaşıdır.

**Kurallar (değiştirilemez):**
1. **Ürün asla tam cevabı varsayılan olarak vermez.** Tam çözüm yalnızca Bölüm 6'daki politika kilidi açıksa gösterilir.
2. **Her LLM çıktısı kullanıcıya gitmeden önce** (a) cevap sızıntı kontrolünden, (b) çocuk güvenliği filtresinden geçer.
3. **Çocuğun kişisel verisi (ad, okul, adres, telefon, e-posta, fotoğraftaki yüz) LLM sağlayıcısına gönderilmeden önce maskelenir.**
4. **Çocuk hesabı ebeveyn onayı olmadan oluşturulamaz.**
5. **Reklam yok, üçüncü taraf davranışsal izleme yok** (analitik yalnızca anonimleştirilmiş/ebeveyn onaylı).
6. Matematikte "gizli çözüm" `sympy` ile doğrulanır. LLM'in tek başına ürettiği sayısal sonuca güvenilmez.
7. Her prompt, model adı ve sürümü `prompt_versions` ve `llm_calls` tablolarında kayıtlıdır (yeniden üretilebilirlik).
8. Yeni özellik = test + eval senaryosu + dokümantasyon güncellemesi. Bunlar olmadan iş "bitti" sayılmaz (Bölüm 21.E Definition of Done).

**Çalışma şekli:** Bölüm 15'teki milestone sırasını (M0→M8) izle. Her milestone'un kabul kriterleri vardır. Belirsiz bir karar görürsen Bölüm 20'ye bak, orada yoksa varsayımını yazıp devam et ve `DECISIONS.md` dosyasına ekle.

**Önerilen repo yapısı ve `AGENTS.md` / `CLAUDE.md` içeriği:** Ek 21.D ve 21.E.

---

