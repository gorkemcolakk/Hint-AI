# Hint.ai Asistan Kuralları ve Çalışma İlkeleri

1. **Değiştirilemez Kurallar**:
   - Nihai cevap varsayılan olarak verilmez (L0–L4; L5 yalnızca yetki ve politika kilidi açıksa).
   - Her LLM çıktısı sızıntı + güvenlik kontrolünden geçer.
   - PII LLM'e gitmeden maskelenir; çocuk metni log'a yazılmaz.
   - Ebeveyn rızası olmadan çocuk verisi işlenmez.
   - Sır repoya girmez; reklam/üçüncü taraf izleme SDK'sı yok.
   - Matematik sonuçları SymPy ile doğrulanır.
   - Prompt değişikliği = yeni sürüm + eval + PR.

2. **Teknoloji**:
   - İstemci: Flutter (iOS + Android + Web, tek proje). Next.js YOK.
   - Backend: FastAPI (Python 3.12), PostgreSQL (+pgvector), Redis, SQLAlchemy async, Alembic.

3. **Çalışma ve Token Disiplini**:
   - Milestone sırası M0 -> M8. Onay almadan sonraki milestone'a geçme.
   - docs/archive/ altını ASLA okuma. Tüm repoyu tarama. Sadece ilgili milestone ve referans dokümanları oku.
   - Her milestone için önce 10 satırı geçmeyen plan sun ve kullanıcı onayı bekle.
   - Bitince: 5 satır özet, test sonucu, DECISIONS.md / ASSUMPTIONS.md güncellemeleri, commit mesajı öner.
   - Her milestone bittiğinde README.md'deki Durum tablosunu güncelle ve aynı commit'e dahil et.
   - Commit öncesi ruff check, ruff format --check, mypy ve pytest hepsi çalıştırılmalı (CI hepsini kontrol ediyor).
