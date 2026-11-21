"""İpucu sızıntısı eval'i (A3/M4 kabul kriteri: L0–L3'te teslim edilen ipucunda sızıntı < %1).

Her golden soru için L0–L3 ipucu, uygulamadaki gibi sırayla (önceki ipuçları modele verilerek)
üretilir ve ölçülür:
- Ham kural sızıntısı: modelin ilk yazdığı ipucunu kural katmanı (7a) yakaladı mı?
- Yargıç reddi (--real): kuralı geçen ipucunu LLM yargıç (7b) sızıntılı buldu mu? Gerekçeler
  yazdırılır; prompt ayarı için gereklidir.
- Yedeğe düşme: geçen ipucu çıkmadı, hazır ipucu verildi.
- Teslim edilen sızıntı: çocuğa gidecek ipucunda kural katmanının yakaladığı sızıntı (0 olmalı).

⚠️ Teslim edilen ipuçlarının gerçek sızıntı oranı yalnızca insan incelemesiyle ölçülebilir
(Bölüm 11.3: yargıç insan örneklemiyle kalibre edilir). Bu rapor modelin eğilimini gösterir.

Kullanım (apps/api içinden):
    python -m evals.run_hint_eval                          # demo model, kota harcamaz
    python -m evals.run_hint_eval --real --limit 2         # gerçek model; soru başına ~9 çağrı
    python -m evals.run_hint_eval --real --ids 1,21,41     # belirli sorular
"""

import asyncio
import sys
from collections import Counter
from typing import Any

from app.modules.llm_gateway.demo import DemoLLMProvider, solve_text
from app.modules.llm_gateway.mask import mask_pii
from app.modules.llm_gateway.providers import LLMError
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.problems.service import generate_solution
from app.modules.tutoring import ladder
from app.modules.tutoring.judge import (
    JUDGE_PROMPT,
    JudgeVerdict,
    build_judge_request,
    parse_verdict,
)
from app.modules.tutoring.leak import check_hint
from app.modules.tutoring.service import HINT_PROMPT, MAX_HINT_GENERATIONS, MAX_JUDGE_REJECTIONS
from app.prompts import load_prompt
from evals.run_solution_eval import load_cases

LEVELS = (0, 1, 2, 3)


async def _hint(gateway: LLMGatewayService, request: str) -> str:
    result = await gateway.complete(
        prompt=request,
        purpose="eval",
        system_prompt=load_prompt(HINT_PROMPT),
        prompt_version=HINT_PROMPT,
        temperature=0.7,
        max_tokens=1024,
    )
    return ladder.clean_hint(result.content)


async def _judge(gateway: LLMGatewayService, **fields: Any) -> JudgeVerdict:
    try:
        result = await gateway.complete(
            prompt=build_judge_request(**fields),
            purpose="eval",
            system_prompt=load_prompt(JUDGE_PROMPT),
            prompt_version=JUDGE_PROMPT,
            temperature=0.0,
            max_tokens=768,
        )
    except LLMError as exc:
        return JudgeVerdict(True, f"judge_error:{type(exc).__name__}", 3, error=True)
    return parse_verdict(result.content)


async def run_hint_eval(
    real: bool = False, limit: int | None = None, ids: set[int] | None = None
) -> dict[str, Any]:
    cases = load_cases()
    if ids:
        cases = [case for case in cases if case["id"] in ids]
    if limit:
        cases = cases[:limit]
    gateway = LLMGatewayService() if real else LLMGatewayService(DemoLLMProvider())
    counts: Counter[str] = Counter()
    delivered_leaks: list[str] = []
    rejections: list[str] = []

    for case in cases:
        problem = str(mask_pii(case["text"]).masked_text)
        steps: list[str] = []
        sympy_check = case.get("sympy_check")
        if real:
            try:
                outcome = await generate_solution(problem, gateway, purpose="eval")
            except LLMError as exc:
                print(f"#{case['id']} çözüm hatası: {type(exc).__name__}")
                counts["errors"] += 1
                continue
            steps = outcome.payload.steps if outcome else []
        else:
            solved = solve_text(problem)
            steps = solved["steps"] if solved else []
        answer = case["answer"]
        kind = ladder.problem_kind(problem, sympy_check)
        previous: list[str] = []

        for level in LEVELS:
            counts["levels"] += 1
            request = ladder.build_hint_request(
                problem_text=problem,
                steps=steps,
                final_answer=answer,
                level=level,
                age_band="11-13",
                previous_hints=previous,
                student_message=None,
                frustrated=False,
            )
            delivered: str | None = None
            judge_rejections = 0
            for generation in range(1, MAX_HINT_GENERATIONS + 1):
                try:
                    text = await _hint(gateway, request)
                except LLMError as exc:
                    print(f"#{case['id']} L{level} ipucu hatası: {type(exc).__name__}")
                    counts["errors"] += 1
                    break
                leak = check_hint(
                    text, level=level, final_answer=answer, steps=steps, problem_text=problem
                )
                if generation == 1 and not leak.ok:
                    counts["raw_rule_leaks"] += 1
                if not leak.ok:
                    continue
                if real:
                    verdict = await _judge(
                        gateway,
                        problem_text=problem,
                        final_answer=answer,
                        steps=steps,
                        level=level,
                        hint=text,
                    )
                    if verdict.leak:
                        counts["judge_rejections"] += 1
                        judge_rejections += 1
                        rejections.append(
                            f"#{case['id']} L{level}: {verdict.reason} | ipucu: {text[:140]}"
                        )
                        if verdict.error or judge_rejections >= MAX_JUDGE_REJECTIONS:
                            break
                        continue
                delivered = text
                break
            if delivered is None:
                counts["fallbacks"] += 1
                delivered = ladder.fallback_hint(level, topic=None, support=False, kind=kind)
            final = check_hint(
                delivered, level=level, final_answer=answer, steps=steps, problem_text=problem
            )
            if not final.ok:
                delivered_leaks.append(f"#{case['id']} L{level} {final.reasons}")
            previous.append(delivered)
            if real:
                print(f"#{case['id']:>2} L{level}: {delivered}", flush=True)
                await asyncio.sleep(4.0)  # ücretsiz katmanın dakika sınırı

    total = counts["levels"] or 1
    report: dict[str, Any] = {
        "mode": "real" if real else "demo",
        "prompts": f"{HINT_PROMPT} + {JUDGE_PROMPT}",
        "questions": len(cases),
        "hint_levels": counts["levels"],
        "raw_rule_leak_percent": counts["raw_rule_leaks"] / total * 100,
        "judge_rejections": counts["judge_rejections"],
        "fallback_percent": counts["fallbacks"] / total * 100,
        "errors": counts["errors"],
        "delivered_leaks": delivered_leaks,
        "passed": not delivered_leaks,
    }
    print("\n" + "=" * 50)
    print(f" Hint.ai Ipucu Sizintisi Eval Raporu ({report['mode']}, {report['prompts']})")
    print("=" * 50)
    print(f" Soru / ipucu (L0-L3)       : {len(cases)} / {counts['levels']}")
    print(f" Ham kural sizintisi        : %{report['raw_rule_leak_percent']:.1f} (ilk uretim)")
    print(f" Yargic reddi               : {counts['judge_rejections']}")
    print(f" Yedek ipucuna dusme        : %{report['fallback_percent']:.1f}")
    print(f" Saglayici hatasi           : {counts['errors']}")
    print(f" Teslim edilen sizinti      : {len(delivered_leaks)} (hedef 0)")
    for line in rejections:
        print(f"   red -> {line}")
    print("=" * 50 + "\n")
    return report


def main() -> None:
    real = "--real" in sys.argv
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    ids = (
        {int(x) for x in sys.argv[sys.argv.index("--ids") + 1].split(",")}
        if "--ids" in sys.argv
        else None
    )
    report = asyncio.run(run_hint_eval(real=real, limit=limit, ids=ids))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
