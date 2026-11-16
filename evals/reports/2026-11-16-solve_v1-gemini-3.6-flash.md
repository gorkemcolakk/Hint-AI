# Gizli çözüm eval raporu — solve_v1 / gemini-3.6-flash

- **Tarih:** 2026-11-16
- **Prompt:** `apps/api/app/prompts/solve_v1.md`
- **Model:** `gemini-3.6-flash` (Google AI Studio ücretsiz katman, OpenAI uyumlu uç nokta)
- **Veri seti:** `apps/api/evals/data/golden_math_v1.jsonl` — 60 sentetik soru, 5–8. sınıf
- **Komut:** `python -m evals.run_solution_eval --real`

## Sonuç (kısmi ölçüm)

| | Değer |
|---|---|
| Ölçülen soru | 22 / 60 (#1–#20, #22, #23) |
| SymPy ile doğrulanan | 22 / 22 (%100) |
| Golden cevapla eşleşen | 22 / 22 (%100) |
| Yeniden üretim / geçersiz JSON | 0 / 0 |
| Kota nedeniyle ölçülemeyen | 38 (#21, #24–#60) |

Kapsanan konular: kesirler, ondalık sayılar, yüzdeler, EBOB/EKOK, üslü ve tam sayılar, alan/çevre, üçgende açılar, doğru orantı, basit denklemler (5–6. sınıf).

## Sınırlılıklar

- Ücretsiz katmanın günlük istek kotası (~20) 21. sorudan sonra doldu; 7–8. sınıf konuları (denklemler, köklü sayılar, olasılık, Pisagor) ölçülmedi.
- Ölçülen örnek küçük; Bölüm 11.1'deki ≥ %98 doğruluk hedefi için istatistiksel güven sınırlı.
- Golden set yapay zekâ ile hazırlandı, öğretmen onayından geçmedi.
- Daha yeni modeller (`gemini-3.7-flash`, `gemini-3.8-flash`) ölçüm sırasında yoğunluk nedeniyle yanıt vermedi (503 / zaman aşımı).

## Kalan sorular nasıl ölçülür

Kota sıfırlandığında: `python -m evals.run_solution_eval --real --from 24`
