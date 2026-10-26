# Hint.ai — AI Asistan Talimatları

Hint.ai: 7–17 yaş öğrencilere cevap değil, kademeli ipucu veren AI öğrenme arkadaşı (çocuk verisi içerir).

## Değiştirilemez kurallar
1. Nihai cevap varsayılan olarak verilmez (L0–L4; L5 yalnızca politika kilidi açıksa).
2. Her LLM çıktısı sızıntı + güvenlik kontrolünden geçer.
3. PII LLM'e gitmeden maskelenir; çocuk metni log'a yazılmaz.
4. Ebeveyn rızası olmadan çocuk verisi işlenmez.
5. Sır repoya girmez; reklam/üçüncü taraf izleme SDK'sı yok.
6. Matematik sonuçları SymPy ile doğrulanır.
7. Prompt değişikliği = yeni sürüm + eval + PR.

## Teknoloji
- İstemci: Expo / React Native + react-native-web, TypeScript (iOS + Android + Web, tek proje). Next.js yok.
- Backend: FastAPI / Python 3.12, PostgreSQL (+pgvector), Redis.
- Araçlar: pytest, ruff, mypy, Docker Compose.

## Komutlar
- `make up` / `make down` · `make test` · `make lint`
- `make eval` · `make migrate` · `make client-gen` · `make client-test`

## Çalışma biçimi
- Milestone sırası M0→M8; kabul kriteri karşılanmadan bir sonrakine geçme.
- Her milestone bittiğinde README.md'deki Durum tablosunu güncelle ve aynı commit'e dahil et.
- Commit öncesi ruff check, ruff format --check, mypy ve pytest hepsi çalıştırılmalı (CI hepsini kontrol ediyor).
- Belirsiz karar: docs/INDEX.md'den ilgili bölüme bak; yoksa ASSUMPTIONS.md'ye yaz, ilerle.
- Kritik güvenlik/gizlilik kararını tek başına verme; PR'da ilgili kişiyi etiketle.

## Token disiplini
- docs/archive/ altını asla okuma.
- Bir milestone için sadece docs/milestones/mX.md ve oradaki listelenen bölüm dosyalarını oku.
- Önce 10 satırı geçmeyen plan yaz, onay bekle.

## Definition of Done
- [ ] Kod + testler yeşil · lint/tip kontrolü yeşil
- [ ] Eval regresyonsuz (AI değişikliklerinde) · güvenlik kontrolü
- [ ] Dokümantasyon/OpenAPI güncel · geri alma planı belli
