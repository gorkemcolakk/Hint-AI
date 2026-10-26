## 9. API Tasarımı

REST + SSE (ipucu akışı). Tüm uçlar `/v1/` altında. Kimlik doğrulama: Bearer JWT. Çocuk istemcisi, ebeveynin yetkilendirdiği **kısıtlı çocuk token'ı** ile çalışır.

### 9.1 Uç noktalar

| Alan | Metot & Yol | Açıklama |
|---|---|---|
| Auth | `POST /auth/register` | Ebeveyn/öğretmen kaydı |
| | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` | |
| | `POST /auth/verify-email` | |
| Ebeveyn | `POST /children` | Çocuk profili oluştur (rıza akışı ile) |
| | `GET/PATCH /children/{id}` | Politika, limit, gizlilik seviyesi |
| | `POST /children/{id}/consents` | Rıza ver/geri çek |
| | `POST /children/{id}/device-pairing` | Çocuk cihazı için eşleştirme kodu |
| | `GET /children/{id}/reports` | Haftalık rapor |
| | `GET /children/{id}/export`, `DELETE /children/{id}` | Veri taşıma/silme |
| Tutoring | `POST /sessions` | Oturum başlat |
| | `POST /sessions/{id}/problems` | Soru gönder (metin veya görsel) |
| | `POST /problems/{id}/hints` (SSE) | Sonraki ipucunu iste |
| | `POST /problems/{id}/attempts` | Öğrenci cevabı gönder |
| | `POST /problems/{id}/reveal-solution` | Politika izin veriyorsa |
| | `POST /hints/{id}/feedback` | Faydalı mı |
| Öğretmen | `POST /classrooms`, `GET /classrooms/{id}/heatmap` | |
| | `POST /classrooms/join` | Davet kodu ile (ebeveyn onayı bekler) |
| Faturalama | `POST /billing/checkout`, `POST /billing/webhook` | |
| Admin | `GET /admin/moderation-queue`, `POST /admin/moderation/{id}/action` | |
| | `GET /admin/evals`, `POST /admin/prompts` | |
| Sağlık | `GET /healthz`, `GET /readyz` | |

### 9.2 Örnek: ipucu yanıtı (SSE olay şeması)

```json
{
  "event": "hint",
  "data": {
    "hint_id": "uuid",
    "level": 2,
    "text": "x'i yalnız bırakmak istiyoruz. Önce hangi sayıdan kurtulmak daha kolay olur?",
    "can_request_next": true,
    "attempts_remaining_before_solution_unlock": 1,
    "safety": { "flagged": false }
  }
}
```

### 9.3 API ilkeleri

- İdempotency anahtarı (ödeme webhook'ları, soru gönderimi).
- Oran sınırı: çocuk başına dakikada N istek, IP başına N istek.
- Hata formatı: RFC 7807 problem details.
- Versiyonlama: `/v1`, kırıcı değişiklik `/v2`.
- OpenAPI şeması kod ile birlikte üretilir (FastAPI); TypeScript istemcisi OpenAPI şemasından openapi-typescript ile üretilir (tipler + openapi-fetch).
- İpucu akışı (SSE): istemcide `expo/fetch` streaming ile okunur (alternatif: react-native-sse), web ve mobilde ayrı test edilir.

---

