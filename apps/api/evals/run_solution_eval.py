"""Gizli çözüm + SymPy doğrulama eval'i (M3 kabul kriteri: doğrulama oranı raporlanır).

Varsayılan (CI) mod: model yerine golden set'teki referans çözümler döner; doğrulayıcının ve
cevap anahtarının tutarlılığı ölçülür, hepsinin geçmesi beklenir.
--real: sorular yapılandırılmış LLM sağlayıcısına (LLM_PROVIDER) gider; model doğruluğu raporlanır.
Golden set sentetiktir; gerçek öğrenci verisi içermez.

Kullanım (apps/api içinden): python -m evals.run_solution_eval [--real]
"""

import asyncio
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from app.modules.llm_gateway.mask import mask_pii
from app.modules.llm_gateway.providers import BaseLLMProvider, LLMMessage, LLMResponse
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.problems.service import generate_solution, normalize_problem, status_for
from app.modules.problems.verify import answers_match

GOLDEN_PATH = Path(__file__).parent / "data" / "golden_math_v1.jsonl"


def load_cases(path: Path = GOLDEN_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


class ReferenceProvider(BaseLLMProvider):
    """Golden set'teki referans çözümü model yanıtı gibi döndürür (ağ çağrısı yok)."""

    def __init__(self, cases: list[dict[str, Any]]) -> None:
        self._by_text = {
            normalize_problem(str(mask_pii(case["text"]).masked_text)): case for case in cases
        }

    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        self._validate_messages(messages)
        case = self._by_text[normalize_problem(str(messages[-1].content))]
        payload = {
            "grade": case["grade"],
            "topic": case["topic"],
            "steps": ["Referans çözüm"],
            "final_answer": case["answer"],
            "sympy_check": case["sympy_check"],
        }
        return LLMResponse(json.dumps(payload, ensure_ascii=False), 0, 0, 0)


async def run_solution_eval(real: bool = False) -> dict[str, Any]:
    cases = load_cases()
    gateway = LLMGatewayService() if real else LLMGatewayService(ReferenceProvider(cases))

    statuses: Counter[str] = Counter()
    correct = 0
    unexpected: list[str] = []
    started = time.monotonic()
    for case in cases:
        masked = str(mask_pii(case["text"]).masked_text)
        outcome = await generate_solution(masked, gateway, purpose="eval")
        status = status_for(outcome)
        statuses[status] += 1
        if outcome is not None and answers_match(case["answer"], outcome.payload.final_answer):
            correct += 1
        if status != case.get("expect_status", "verified"):
            unexpected.append(f"#{case['id']} {status}")

    total = len(cases)
    verified_rate = statuses["verified"] / total * 100 if total else 0.0
    accuracy = correct / total * 100 if total else 0.0
    report: dict[str, Any] = {
        "mode": "real" if real else "reference",
        "total_cases": total,
        "statuses": dict(statuses),
        "verified_rate_percent": verified_rate,
        "accuracy_percent": accuracy,
        "unexpected": unexpected,
        # Referans modda her şey beklendiği gibi olmalı; gerçek modda yalnızca rapor üretilir.
        "passed": real or (not unexpected and correct == total),
    }

    print("\n" + "=" * 50)
    print(f" Hint.ai Gizli Çözüm Eval Raporu ({report['mode']})")
    print("=" * 50)
    print(f" Soru sayısı           : {total}")
    print(f" Durumlar              : {dict(statuses)}")
    print(f" SymPy doğrulama oranı : %{verified_rate:.1f}")
    print(f" Cevap doğruluğu       : %{accuracy:.1f} (golden cevaba göre)")
    print(f" Beklenmeyen durumlar  : {', '.join(unexpected) or 'yok'}")
    print(f" Süre                  : {time.monotonic() - started:.1f} sn")
    print("=" * 50 + "\n")
    return report


def main() -> None:
    report = asyncio.run(run_solution_eval(real="--real" in sys.argv))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
