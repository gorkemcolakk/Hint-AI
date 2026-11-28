"""Gizli çözüm üretimi ve doğrulaması (Hint Engine adım 3 ve 4).

Akış: soru maskelenir → aynı soru için doğrulanmış çözüm önbellekte varsa kullanılır →
yoksa LLM yapılandırılmış çözüm üretir → SymPy bağımsız kontrol eder → tutmazsa bir kez
yeniden üretilir → yine tutmazsa soru düşük güvenli işaretlenir. Çözüm öğrenciye dönmez.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.llm_gateway.mask import mask_pii
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.problems.models import HiddenSolution, Problem
from app.modules.problems.verify import VerificationResult, verify_solution
from app.prompts import load_prompt

SOLVE_PROMPT = "solve_v1"
MAX_SOLVE_ATTEMPTS = 2


class DailyProblemLimitExceededError(Exception):
    """Ebeveynin belirlediği günlük yeni soru sınırı aşıldığında fırlatılır (Bölüm 5.5)."""


class SolutionPayload(BaseModel):
    """LLM'in döndürmesi gereken çözüm biçimi (app/prompts/solve_v1.md)."""

    grade: int | None = Field(default=None, ge=1, le=12)
    topic: str | None = Field(default=None, max_length=120)
    steps: list[str] = Field(default_factory=list, max_length=20)
    final_answer: str = Field(min_length=1, max_length=200)
    sympy_check: dict[str, Any] | None = None


@dataclass(frozen=True)
class SolutionOutcome:
    payload: SolutionPayload
    verification: VerificationResult
    model: str
    attempts: int


def normalize_problem(masked_text: str) -> str:
    return " ".join(masked_text.lower().split())


def problem_hash(masked_text: str) -> str:
    return hashlib.sha256(normalize_problem(masked_text).encode("utf-8")).hexdigest()


def parse_solution(content: str) -> SolutionPayload | None:
    """Model yanıtından çözüm JSON'unu çıkarır; kod bloğu sarmalını tolere eder."""
    text = content.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return SolutionPayload.model_validate(json.loads(text[start : end + 1]))
    except (json.JSONDecodeError, ValidationError):
        return None


async def generate_solution(
    masked_text: str,
    gateway: LLMGatewayService,
    *,
    purpose: str = "solve",
    child_id: uuid.UUID | None = None,
    db: AsyncSession | None = None,
) -> SolutionOutcome | None:
    """Çözüm üretir ve doğrular. Geçerli JSON hiç gelmezse None döner."""
    best: SolutionOutcome | None = None
    for attempt in range(1, MAX_SOLVE_ATTEMPTS + 1):
        result = await gateway.complete(
            prompt=masked_text,
            purpose=purpose,
            system_prompt=load_prompt(SOLVE_PROMPT),
            prompt_version=SOLVE_PROMPT,
            child_id=child_id,
            db=db,
            temperature=0.2,
            max_tokens=2500,
        )
        payload = parse_solution(result.content)
        if payload is None:
            continue
        verification = verify_solution(payload.sympy_check, payload.final_answer)
        best = SolutionOutcome(payload, verification, result.model, attempt)
        # Yalnızca SymPy ile çelişen çözüm yeniden üretilir; doğrulanamayan soru tekrar sorulmaz.
        if verification.status != "mismatch":
            break
    return best


def status_for(outcome: SolutionOutcome | None) -> str:
    if outcome is None:
        return "failed"
    return {
        "verified": "verified",
        "mismatch": "low_confidence",
        "unverifiable": "unverifiable",
    }[outcome.verification.status]


async def create_problem(
    db: AsyncSession,
    child_id: uuid.UUID,
    text: str,
    gateway: LLMGatewayService,
    *,
    daily_limit: int | None = None,
) -> tuple[Problem, HiddenSolution | None]:
    """Öğrencinin sorusunu kaydeder ve gizli çözümünü hazırlar."""
    if daily_limit is not None:
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = int(
            await db.scalar(
                select(func.count(Problem.id)).where(
                    Problem.child_id == child_id,
                    Problem.created_at >= today_start,
                )
            )
            or 0
        )
        if today_count >= daily_limit:
            raise DailyProblemLimitExceededError()

    masked = str(mask_pii(text).masked_text)
    digest = problem_hash(masked)

    from app.core.config import settings

    cache_query = select(HiddenSolution).where(
        HiddenSolution.problem_hash == digest, HiddenSolution.verified.is_(True)
    )
    if settings.llm_provider not in ("mock", "demo"):
        cache_query = cache_query.where(HiddenSolution.model.notin_(("mock", "demo")))
    solution = cast(
        HiddenSolution | None,
        await db.scalar(cache_query.order_by(HiddenSolution.created_at.desc()).limit(1)),
    )
    status = "verified"
    if solution is None:
        outcome = await generate_solution(masked, gateway, child_id=child_id, db=db)
        status = status_for(outcome)
        if outcome is not None:
            solution = HiddenSolution(
                problem_hash=digest,
                grade=outcome.payload.grade,
                topic=outcome.payload.topic,
                steps=outcome.payload.steps,
                final_answer=outcome.payload.final_answer,
                sympy_check=outcome.payload.sympy_check,
                verified=outcome.verification.status == "verified",
                verification_note=outcome.verification.note,
                prompt_version=SOLVE_PROMPT,
                model=outcome.model,
            )
            db.add(solution)
            await db.flush()

    problem = Problem(
        child_id=child_id,
        masked_text=masked,
        problem_hash=digest,
        status=status,
        solution_id=solution.id if solution is not None else None,
    )
    db.add(problem)
    await db.commit()
    await db.refresh(problem)
    return problem, solution
