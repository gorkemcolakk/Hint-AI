# Karar Günlüğü

> Kaynak: docs/master-plan.md Bölüm 20. Yeni kararlar buraya eklenir.

| # | Karar | Sonuç | Tarih | Karar sahibi |
|---|---|---|---|---|
| D7 | Mobil/Web yaklaşımı | Flutter (iOS + Android + Web, tek istemci) — **D7-r ile değiştirildi** | 2026-10-16 | BM-2 + BM-1 |
| D8 | Backend çatısı | FastAPI | 2026-10-16 | BM-1 |
| M0-1 | PostgreSQL sürücüsü | psycopg 3 (binary); SQLAlchemy/asyncpg M2+ ile gerekince eklenir | 2026-10-16 | BM-1 |
| M0-2 | Postgres imajı | postgres:16-alpine; pgvector ihtiyacında pgvector/pgvector:pg16'ya geçilir | 2026-10-16 | BM-1 |
| M1-1 | Login/register brute-force sınırlaması | TODO: M1'e alınmadı; rate limit sonraki milestone'da eklenecek | 2026-10-16 | BM-1 |
| M1-2 | Refresh token | Opaque token; SHA-256 hash'i `refresh_tokens` tablosunda; logout'ta iptal, refresh'te rotasyon | 2026-10-16 | BM-1 |
| M1-3 | Pairing kodu | Kod SHA-256 hash olarak saklanır; 10 dk geçerlilik; kod başına en fazla 5 hatalı deneme | 2026-10-16 | BM-1 |
| M1-4 | Çocuk tokenı | Kısa ömürlü (30 dk, refresh yok); her istekte `purpose='service'` rızası kontrol edilir | 2026-10-16 | BM-1 |
| M1-5 | E-posta saklama | CITEXT yerine küçük harf normalizasyonu + unique String kullanıldı | 2026-10-16 | BM-1 |
| M1-6 | E-posta doğrulama | Stub (gönderim yok); login doğrulanmamış e-postayla çalışır | 2026-10-16 | BM-1 |
| M2-1 | LLM Sağlayıcı mimarisi | BaseLLMProvider soyutlaması + MockProvider (varsayılan) + OpenAI uyumlu HttpLLMProvider (Google Gemini) | 2026-10-17 | BM-1 |
| M2-2 | PII Maskeleme | TCKN checksum doğrulamalı, TR telefon, e-posta, TR IBAN, sezgisel ad/okul; sağlayıcı katmanında zorunlu MaskedText | 2026-10-17 | BM-1 |
| M2-3 | llm_calls gizliliği | Çocuk metni, prompt veya yanıt asla DB ve loglara yazılmaz; yalnızca token, maliyet ve durum saklanır | 2026-10-17 | BM-1 |
| M2-4 | Retry & Timeout | Yalnızca timeout, 5xx ve 429 için retry (maks 1); 4xx için hemen hata fırlatılır; maliyet config tablosundan hesaplanır | 2026-10-17 | BM-1 |
| D7-r | Mobil/Web yaklaşımı (D7 revizyonu) | Expo (React Native + react-native-web, Expo Router), TypeScript; iOS + Android + Web tek istemci. Gerekçe: web'de erişilebilirlik ve hızlı ilk açılış (Flutter web sayfayı canvas'a çizer, R16), panel ve matematik için geniş React ekosistemi; istemci kodu yokken değiştirildi. Göze alınan: geçiş gecikmesi riski (R18), mobilde matematik gösterimi WebView ile. Next.js yok. Ayrıntı: Bölüm 3.7 | 2026-10-26 | BM-2 + BM-1 |
| D7-r1 | İstemci araç seti | TanStack Query (sunucu durumu), openapi-typescript + openapi-fetch (tipli API istemcisi), expo-secure-store (token), Jest + React Native Testing Library, e2e: Playwright (web) + Maestro (mobil). M1.5'te kesinleşir | 2026-10-26 | BM-2 |
| M1.5-1 | Web'de token saklama | Token'lar web'de yalnızca bellekte (localStorage yok); sayfa yenilenince oturum kapanır. Güvenlik dokümanındaki httpOnly cookie akışı M7'de | 2026-10-26 | BM-1 + BM-2 |
| M1.5-2 | Çocuk oturum süresi | M1-4 korunur (30 dk, yenileme yok); ebeveynin iptal edebileceği uzun ömürlü cihaz oturumu M6'da tasarlanır | 2026-10-26 | BM-1 + BM-2 |
| M1.5-3 | Cihaz eşleştirme akışı | Ebeveyn tek kullanımlık bağlantı (child_id + kod, 10 dk) paylaşır; çocuk kod ya da şifre yazmaz. Aynı cihazda "çocuk moduna geçir" ebeveynin refresh token'ını sunucuda iptal eder. QR ve yalnızca kodla giriş M6'da | 2026-10-26 | BM-2 |
| M1.5-4 | CORS | Yalnızca `HINT_CORS_ORIGINS` listesindeki origin'ler; credentials kapalı (kimlik Bearer header'da) | 2026-10-26 | BM-1 |
| M1.5-5 | Ebeveynin çocuk listesi | API tasarımında olmayan `GET /v1/children` eklendi; ebeveyn yalnızca kendi çocuklarını görür | 2026-10-26 | BM-1 |
| M1.5-6 | API sözleşmesi | `apps/client/openapi.json` ve üretilen tipler repoda; CI, şemanın ve tiplerin koddan sapmadığını kontrol eder | 2026-10-26 | BM-1 + BM-2 |
| M1.5-7 | Oturuma göre yönlendirme | Erişim kuralları kök layout'ta `Stack.Protected` ile tek yerde; koruması kalkan ekranlar gezinme geçmişinden silinir | 2026-10-26 | BM-2 |
| M1.5-8 | İstemci sürümleri (D7-r1 kesinleşti) | Expo SDK 58 · React 19.3 · RN 0.88 · TypeScript 6.0 · TanStack Query 5 · openapi-fetch 0.17 · openapi-typescript 7.13 (TS 6 için `overrides`) · Jest 30 + jest-expo + RNTL 14 · ESLint 9. E2e araçları (Playwright, Maestro) M6'ya kaldı | 2026-10-26 | BM-2 |
