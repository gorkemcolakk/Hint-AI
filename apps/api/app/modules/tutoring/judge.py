"""LLM sızıntı yargıcı (Hint Engine adım 7b). Kural katmanının (7a) ÜSTÜNE eklenir.

Fail-closed: model hatası, geçersiz JSON veya belirsiz yanıt "sızıntı var" sayılır; ipucu
yayınlanmaz, yeniden üretilir ya da hazır güvenli ipucu verilir (Bölüm 7.7).
"""

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.llm_gateway.providers import ConsentRequiredError, LLMError
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.tutoring.ladder import LEVEL_NAMES
from app.prompts import load_prompt

JUDGE_PROMPT = "judge_v3"
# Gemini 2.5 / 3.x düşünme token'ları da max_tokens bütçesinden düşer; 768 sınırında JSON
# kesildiği için yeterli marj bırakılır.
JUDGE_MAX_TOKENS = 2048


@dataclass(frozen=True)
class JudgeVerdict:
    leak: bool
    reason: str
    severity: int
    # Model yanıt vermedi ya da yanıt okunamadı (fail-closed).
    error: bool = False


def build_judge_request(
    *, problem_text: str, final_answer: str, steps: Sequence[str], level: int, hint: str
) -> str:
    return "\n".join(
        [
            f"SORU: {problem_text}",
            f"GİZLİ CEVAP: {final_answer}",
            "GİZLİ ÇÖZÜM ADIMLARI:",
            *(f"- {step}" for step in steps),
            f"SEVİYE: L{level} ({LEVEL_NAMES[level]})",
            f"İPUCU: {hint}",
        ]
    )


def parse_verdict(content: str) -> JudgeVerdict:
    text = content.strip()
    start, end = text.find("{"), text.rfind("}")
    try:
        data = json.loads(text[start : end + 1]) if start != -1 and end > start else None
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict) or not isinstance(data.get("leak"), bool):
        return JudgeVerdict(True, "judge_unparseable", 3, error=True)
    severity = data.get("severity")
    return JudgeVerdict(
        leak=data["leak"],
        reason=str(data.get("reason", ""))[:200],
        severity=severity if isinstance(severity, int) else (3 if data["leak"] else 0),
    )


async def judge_hint(
    gateway: LLMGatewayService,
    db: AsyncSession,
    *,
    child_id: uuid.UUID,
    problem_text: str,
    final_answer: str,
    steps: Sequence[str],
    level: int,
    hint: str,
) -> JudgeVerdict:
    request = build_judge_request(
        problem_text=problem_text, final_answer=final_answer, steps=steps, level=level, hint=hint
    )
    judge_model = settings.llm_judge_model.strip() or None
    for attempt in range(2):
        prompt_text = (
            request
            if attempt == 0
            else f"{request}\nHATIRLATMA: Yalnızca geçerli tek satır JSON döndür."
        )
        try:
            result = await gateway.complete(
                prompt=prompt_text,
                purpose="leak_judge",
                system_prompt=load_prompt(JUDGE_PROMPT),
                prompt_version=JUDGE_PROMPT,
                child_id=child_id,
                db=db,
                model_override=judge_model,
                temperature=0.0,
                max_tokens=JUDGE_MAX_TOKENS,
            )
        except ConsentRequiredError:
            raise
        except LLMError as exc:
            return JudgeVerdict(True, f"judge_error:{type(exc).__name__}", 3, error=True)
        verdict = parse_verdict(result.content)
        if not verdict.error:
            return verdict
    return verdict
