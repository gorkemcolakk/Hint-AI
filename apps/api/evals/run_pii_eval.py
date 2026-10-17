"""PII Maskeleme ve LLM Gateway Eval Çalıştırıcısı.

apps/api/evals/data/pii_eval_cases.jsonl veri setindeki girdileri
maskeleme ve Mock sağlayıcı üzerinden geçirir; sağlayıcıya hiçbir ham
PII verisinin sızmadığını doğrular (Hedef: Sızan PII sayısı = 0).
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from app.modules.llm_gateway.providers import MockLLMProvider
from app.modules.llm_gateway.service import LLMGatewayService


async def run_pii_eval(data_path: Path | None = None) -> dict[str, Any]:
    """Eval veri setini çalıştırır ve metrikleri döner."""
    if data_path is None:
        data_path = Path(__file__).parent / "data" / "pii_eval_cases.jsonl"

    if not data_path.exists():
        raise FileNotFoundError(f"Eval veri seti dosyası bulunamadı: {data_path}")

    cases: list[dict[str, Any]] = []
    with data_path.open(encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                cases.append(json.loads(line_str))

    mock_provider = MockLLMProvider()
    service = LLMGatewayService(provider=mock_provider)

    total_cases = len(cases)
    leaked_pii_count = 0
    all_detected_types: set[str] = set()

    for idx, case in enumerate(cases):
        raw_input = case["input"]
        raw_pii_list = case.get("raw_pii", [])

        # Gateway üzerinden çağrı yap
        result = await service.complete(
            prompt=raw_input,
            purpose="eval",
            prompt_version="eval_v1",
        )

        all_detected_types.update(result.pii_detected_types)

        # Provider'a giden mesajları incele
        # mock_provider.calls[idx] o çağrıda iletilen LLMMessage listesidir
        sent_messages = mock_provider.calls[idx]
        sent_content = " ".join(str(m.content) for m in sent_messages)

        # Ham PII sağlayıcıya ulaştı mı?
        for pii in raw_pii_list:
            if pii in sent_content:
                leaked_pii_count += 1
                print(f"[UYARI] Sızıntı tespit edildi! ID={case['id']}, Değer={pii}")

    passed = leaked_pii_count == 0
    leak_rate = (leaked_pii_count / total_cases) * 100 if total_cases > 0 else 0.0

    report = {
        "total_cases": total_cases,
        "leaked_pii_count": leaked_pii_count,
        "leak_rate_percent": leak_rate,
        "detected_types": sorted(all_detected_types),
        "passed": passed,
    }

    # Konsol raporu bas
    print("\n" + "=" * 50)
    print(" Hint.ai PII Masking & Gateway Eval Raporu")
    print("=" * 50)
    print(f" Toplam Test Senaryosu : {total_cases}")
    print(f" Tespit Edilen Türler  : {', '.join(sorted(all_detected_types))}")
    print(f" Sızan PII Sayısı      : {leaked_pii_count} (Hedef: 0)")
    print(f" Sızıntı Oranı         : %{leak_rate:.1f}")
    print(f" Değerlendirme         : {'GEÇTİ (PASS)' if passed else 'BAŞARISIZ (FAIL)'}")
    print("=" * 50 + "\n")

    return report


def main() -> None:
    report = asyncio.run(run_pii_eval())
    if not report["passed"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
