"""İpucu merdiveni akışı (Hint Engine adım 5–7).

İpucu isteği: seviye belirlenir → model gizli çözümü bilerek ipucu yazar → kural tabanlı sızıntı
kontrolü → sızıntı varsa yeniden üretilir (en fazla MAX_HINT_GENERATIONS) → yine sızıyorsa veya
model erişilemiyorsa hazır güvenli ipucu verilir. Nihai cevap hiçbir yanıtta dönmez.

Deneme: öğrencinin cevabı SymPy ile gizli çözüme karşı kontrol edilir; doğruysa soru çözülür,
son ipucundan beri 2 yanlış denemede merdiven bir basamak otomatik yükselir.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.auth_consent.models import ChildProfile
from app.modules.llm_gateway.mask import mask_pii
from app.modules.llm_gateway.providers import ConsentRequiredError, LLMError
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.problems.models import HiddenSolution, Problem
from app.modules.problems.verify import answers_match, parse_answers, sympy_answer
from app.modules.safety.models import record_event
from app.modules.safety.output import check_output
from app.modules.tutoring import ladder
from app.modules.tutoring.judge import judge_hint
from app.modules.tutoring.leak import check_hint
from app.modules.tutoring.models import Attempt, Hint
from app.prompts import load_prompt

HINT_PROMPT = "hint_v3"
HINT_MAX_TOKENS = 2048
MAX_HINT_GENERATIONS = 3
# Her yargıç reddi 2 çağrıya mal olur (ipucu + yargıç); kotayı korumak için sınırlı.
MAX_JUDGE_REJECTIONS = 2


@dataclass(frozen=True)
class AttemptOutcome:
    attempt: Attempt
    solved: bool
    feedback: str
    hint: Hint | None


async def get_child_problem(
    db: AsyncSession, child_id: uuid.UUID, problem_id: uuid.UUID
) -> Problem:
    problem = cast(Problem | None, await db.get(Problem, problem_id))
    if problem is None or problem.child_id != child_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Soru bulunamadı")
    return problem


async def load_solution(db: AsyncSession, problem: Problem) -> HiddenSolution | None:
    if problem.solution_id is None:
        return None
    return cast(HiddenSolution | None, await db.get(HiddenSolution, problem.solution_id))


def answer_key(problem: Problem, solution: HiddenSolution) -> str:
    """Öğrencinin cevabının karşılaştırılacağı değer.

    SymPy modelle çeliştiyse (low_confidence) modelin cevabı muhtemelen yanlıştır; SymPy'ın
    bağımsız bulduğu sonuç kullanılır.
    """
    if problem.status == "low_confidence":
        return sympy_answer(solution.sympy_check) or solution.final_answer
    return solution.final_answer


def forbidden_answers(problem: Problem, solution: HiddenSolution) -> str:
    """İpucunda geçmemesi gereken cevaplar: düşük güvenli soruda hem modelin hem SymPy'ın
    cevabı; yalnızca modelinkini yasaklamak gerçek cevabın sızmasına izin verirdi."""
    computed = sympy_answer(solution.sympy_check) if problem.status == "low_confidence" else None
    return f"{solution.final_answer}; {computed}" if computed else solution.final_answer


async def list_hints(db: AsyncSession, problem_id: uuid.UUID) -> list[Hint]:
    rows = await db.scalars(
        select(Hint).where(Hint.problem_id == problem_id).order_by(Hint.created_at, Hint.level)
    )
    return list(rows)


async def count_attempts(db: AsyncSession, problem_id: uuid.UUID) -> int:
    count = await db.scalar(select(func.count(Attempt.id)).where(Attempt.problem_id == problem_id))
    return int(count or 0)


def _require_open(problem: Problem) -> None:
    if problem.state != "open":
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu soru zaten çözüldü")


async def _generate_hint_text(
    db: AsyncSession,
    *,
    child: ChildProfile,
    problem: Problem,
    solution: HiddenSolution,
    level: int,
    previous: list[str],
    student_message: str | None,
    frustrated: bool,
    gateway: LLMGatewayService,
) -> tuple[str | None, dict[str, object], uuid.UUID | None]:
    """Sızıntı kontrolünü geçen bir model ipucu üretmeye çalışır; olmazsa metin None döner."""
    request = ladder.build_hint_request(
        problem_text=problem.masked_text,
        steps=solution.steps,
        final_answer=forbidden_answers(problem, solution),
        level=level,
        age_band=child.age_band,
        previous_hints=previous,
        student_message=student_message,
        frustrated=frustrated,
    )
    reasons: list[str] = []
    judge_log: list[dict[str, object]] = []
    call_id: uuid.UUID | None = None

    def report(generation: int, passed: bool, judge: dict[str, object] | None) -> dict[str, object]:
        return {
            "rule_pass": passed,
            "judge": judge,
            "generations": generation,
            "reasons": reasons,
        }

    for generation in range(1, MAX_HINT_GENERATIONS + 1):
        try:
            result = await gateway.complete(
                prompt=request,
                purpose="hint",
                system_prompt=load_prompt(HINT_PROMPT),
                prompt_version=HINT_PROMPT,
                child_id=child.id,
                db=db,
                temperature=0.7,
                # Düşünme token'ları da bu sınırdan düşer; küçük sınır yanıtı keser.
                max_tokens=HINT_MAX_TOKENS,
            )
        except ConsentRequiredError:
            raise
        except LLMError as exc:
            # Kesinti veya günlük limit: çocuk takılı kalmasın, maliyetsiz yedek ipucu verilir.
            reasons.append(f"llm_error:{type(exc).__name__}")
            return None, report(generation, False, None), None
        call_id = result.call_id
        text = ladder.clean_hint(result.content)
        if not text:
            reasons.append("empty")
            continue
        # 7a: kural tabanlı sızıntı + 8: çıktı güvenliği (ucuz, deterministik).
        leak = check_hint(
            text,
            level=level,
            final_answer=forbidden_answers(problem, solution),
            steps=solution.steps,
            problem_text=problem.masked_text,
        )
        unsafe = check_output(text)
        if not leak.ok or unsafe:
            reasons += leak.reasons + unsafe
            if unsafe:
                await record_event(
                    db,
                    child_id=child.id,
                    problem_id=problem.id,
                    stage="output",
                    source="hint_output",
                    category=unsafe[0].split(":")[0],
                    severity=2,
                    action="regenerated",
                )
            continue
        if not settings.leak_judge_enabled:
            return text, report(generation, True, None), call_id
        # 7b: LLM yargıç; hata veya belirsizlik sızıntı sayılır (fail-closed).
        verdict = await judge_hint(
            gateway,
            db,
            child_id=child.id,
            problem_text=problem.masked_text,
            final_answer=forbidden_answers(problem, solution),
            steps=solution.steps,
            level=level,
            hint=text,
        )
        # Gerekçe yalnızca iç kayıtta tutulur (çocuğa dönmez); prompt'u ayarlamak için gerekli.
        judge_info: dict[str, object] = {
            "leak": verdict.leak,
            "severity": verdict.severity,
            "error": verdict.error,
            "reason": verdict.reason,
        }
        judge_log.append(judge_info)
        if not verdict.leak:
            accepted = {**judge_info, "earlier_rejections": judge_log[:-1]}
            return text, report(generation, True, accepted), call_id
        reasons.append("judge_error" if verdict.error else f"judge_leak:{verdict.severity}")
        if verdict.error or len(judge_log) >= MAX_JUDGE_REJECTIONS:
            # Yargıç çalışmıyorsa ya da üst üste reddediyorsa: güvenli yedek ipucu.
            return None, report(generation, True, {"rejections": judge_log}), call_id
    return None, report(MAX_HINT_GENERATIONS, False, None), call_id


async def _give_hint(
    db: AsyncSession,
    *,
    child: ChildProfile,
    problem: Problem,
    student_message: str | None,
    gateway: LLMGatewayService,
) -> Hint:
    solution = await load_solution(db, problem)
    raw_frustrated = ladder.is_frustrated(student_message)
    level = ladder.next_level(
        problem.current_hint_level, status=problem.status, frustrated=raw_frustrated
    )
    previous = [hint.content for hint in await list_hints(db, problem.id)]
    # Aynı destek cümlesinin her basamakta robotik biçimde tekrarlanmasını önle.
    already_supported = any(ladder.SUPPORT_LINE in prev for prev in previous)
    show_support = raw_frustrated and not already_supported
    masked_message = str(mask_pii(student_message).masked_text) if student_message else None

    text: str | None = None
    leak_check: dict[str, object] = {
        "rule_pass": False,
        "judge": None,
        "generations": 0,
        "reasons": ["no_solution"],
    }
    call_id: uuid.UUID | None = None
    if solution is not None:
        text, leak_check, call_id = await _generate_hint_text(
            db,
            child=child,
            problem=problem,
            solution=solution,
            level=level,
            previous=previous,
            student_message=masked_message,
            frustrated=show_support,
            gateway=gateway,
        )

    source = "llm"
    if text is None:
        source = "fallback"
        kind = ladder.problem_kind(problem.masked_text, solution.sympy_check if solution else None)
        text = ladder.fallback_hint(
            level, topic=solution.topic if solution else None, support=show_support, kind=kind
        )
        if solution is not None:
            # L4'te önce sızıntısız somut ikiz örnekleri, sonra rakamsız yedeği dene.
            candidates = (
                ladder.worked_l4_candidates(kind, support=show_support) if level == 4 else []
            ) + [
                text,
                ladder.fallback_hint(level, topic=None, support=show_support, kind=kind),
            ]
            for candidate in candidates:
                safe = check_hint(
                    candidate,
                    level=level,
                    final_answer=forbidden_answers(problem, solution),
                    steps=solution.steps,
                    problem_text=problem.masked_text,
                )
                if safe.ok:
                    text = candidate
                    break
        if level >= ladder.max_level_for(problem.status) and problem.status != "verified":
            text = f"{text} {ladder.UNVERIFIED_NOTE}"

    hint = Hint(
        problem_id=problem.id,
        level=level,
        content=text,
        source=source,
        leak_check=leak_check,
        prompt_version=HINT_PROMPT if source == "llm" else None,
        llm_call_id=call_id if source == "llm" else None,
    )
    db.add(hint)
    problem.current_hint_level = level
    await db.commit()
    await db.refresh(hint)
    return hint


async def request_hint(
    db: AsyncSession,
    child: ChildProfile,
    problem_id: uuid.UUID,
    message: str | None,
    gateway: LLMGatewayService,
) -> Hint:
    problem = await get_child_problem(db, child.id, problem_id)
    _require_open(problem)
    return await _give_hint(
        db, child=child, problem=problem, student_message=message, gateway=gateway
    )


def normalize_student_answer(text: str, expected_count: int) -> str | None:
    """Öğrencinin yazdığı cevabı SymPy'ın okuyabileceği biçime getirir; okunamazsa None."""
    candidate = re.sub(r"(\d),(\d)", r"\1.\2", text.strip())  # Türkçe ondalık virgül
    candidate = candidate.replace("−", "-").rstrip(".!? ")
    if expected_count > 1:
        candidate = re.sub(r"\s*(?:,|\bve\b|\bya da\b|\bveya\b)\s*", "; ", candidate)
    for option in (candidate, _only_numbers(candidate, expected_count)):
        if not option:
            continue
        try:
            parse_answers(option)
        except Exception:
            continue
        return option
    return None


def _only_numbers(text: str, expected_count: int) -> str | None:
    """'cevabım 5' gibi metinlerden sayıları çıkarır (beklenen adet kadar sayı varsa)."""
    numbers = re.findall(r"-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?", text)
    return "; ".join(numbers) if len(numbers) == expected_count else None


async def submit_attempt(
    db: AsyncSession,
    child: ChildProfile,
    problem_id: uuid.UUID,
    answer: str,
    gateway: LLMGatewayService,
) -> AttemptOutcome:
    problem = await get_child_problem(db, child.id, problem_id)
    _require_open(problem)
    solution = await load_solution(db, problem)
    masked = str(mask_pii(answer).masked_text)

    is_correct: bool | None = None
    if solution is not None:
        try:
            expected_count = len(parse_answers(answer_key(problem, solution)))
        except Exception:
            expected_count = 1
        normalized = normalize_student_answer(masked, expected_count)
        if normalized is not None:
            is_correct = answers_match(answer_key(problem, solution), normalized)

    attempt = Attempt(problem_id=problem.id, answer_masked=masked, is_correct=is_correct)
    db.add(attempt)

    if is_correct:
        problem.state = "solved"
        problem.solved_at = datetime.now(UTC)
        hints_used = len(await list_hints(db, problem.id))
        await db.commit()
        await db.refresh(attempt)
        feedback = (
            "Harika! Hiç ipucu almadan kendin çözdün."
            if hints_used == 0
            else f"Harika! {hints_used} ipucuyla kendin çözdün."
        )
        return AttemptOutcome(attempt, True, feedback, None)

    await db.commit()
    await db.refresh(attempt)
    if solution is None:
        return AttemptOutcome(
            attempt, False, "Bu soruyu şu an kontrol edemiyorum; öğretmenine danışabilirsin.", None
        )
    if is_correct is None:
        return AttemptOutcome(
            attempt,
            False,
            "Cevabını sayı ya da ifade olarak yazar mısın? Örneğin 5, -2 ya da 3/4.",
            None,
        )

    feedback = "Henüz tam değil, bir de şuna bakalım."
    if problem.status != "verified":
        feedback = f"{feedback} {ladder.UNVERIFIED_NOTE}"
    hint: Hint | None = None
    if (
        await _wrong_attempts_since_last_hint(db, problem)
        >= ladder.WRONG_ATTEMPTS_BEFORE_ESCALATION
    ):
        current = problem.current_hint_level
        if current is None or current < ladder.max_level_for(problem.status):
            hint = await _give_hint(
                db, child=child, problem=problem, student_message=None, gateway=gateway
            )
            feedback = "Henüz tam değil. Sana yeni bir ipucu hazırladım."
    return AttemptOutcome(attempt, False, feedback, hint)


async def _wrong_attempts_since_last_hint(db: AsyncSession, problem: Problem) -> int:
    last_hint_at = await db.scalar(
        select(func.max(Hint.created_at)).where(Hint.problem_id == problem.id)
    )
    query = select(func.count(Attempt.id)).where(
        Attempt.problem_id == problem.id, Attempt.is_correct.is_(False)
    )
    if last_hint_at is not None:
        query = query.where(Attempt.created_at > last_hint_at)
    return int(await db.scalar(query) or 0)


async def set_hint_feedback(
    db: AsyncSession, child_id: uuid.UUID, hint_id: uuid.UUID, helpful: bool
) -> Hint:
    """Öğrencinin kendi sorusuna ait ipucuna faydalı/anlaşılmadı geri bildirimi kaydeder."""
    row = (
        await db.execute(
            select(Hint, Problem.child_id)
            .join(Problem, Problem.id == Hint.problem_id)
            .where(Hint.id == hint_id)
        )
    ).first()
    if row is None or row[1] != child_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "İpucu bulunamadı")
    hint = row[0]
    hint.helpful = helpful
    await db.commit()
    await db.refresh(hint)
    return hint
