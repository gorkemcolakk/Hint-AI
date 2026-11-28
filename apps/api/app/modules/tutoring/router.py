import json
import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth_consent.deps import get_current_child
from app.modules.auth_consent.models import ChildProfile
from app.modules.llm_gateway.providers import ConsentRequiredError, DailyLimitExceededError
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.problems.router import get_llm_gateway
from app.modules.safety.service import SafetyNotice, screen_input
from app.modules.tutoring import ladder, service
from app.modules.tutoring.models import Hint

tutoring_router = APIRouter(prefix="/v1/problems", tags=["tutoring"])
hints_router = APIRouter(prefix="/v1/hints", tags=["tutoring"])

Child = Annotated[ChildProfile, Depends(get_current_child)]
Db = Annotated[AsyncSession, Depends(get_db)]
Gateway = Annotated[LLMGatewayService, Depends(get_llm_gateway)]

_CONSENT_MESSAGE = "Yapay zekâ ile işleme izni yok. Ebeveyninden bu izni vermesini iste."
_DAILY_LIMIT_MESSAGE = "Bugünlük yapay zekâ hakkın doldu, yarın devam edelim."


class HintOut(BaseModel):
    """Öğrenciye giden ipucu. Sızıntı kontrolü ayrıntıları ve gizli çözüm bilerek yoktur."""

    id: uuid.UUID
    level: int
    level_name: str
    text: str


class ProblemDetail(BaseModel):
    id: uuid.UUID
    text: str = Field(description="Sorunun PII maskelenmiş hali")
    status: str
    topic: str | None
    state: str
    current_hint_level: int | None
    max_hint_level: int
    can_request_hint: bool
    hints: list[HintOut]
    attempts_count: int


class HintRequest(BaseModel):
    message: str | None = Field(default=None, max_length=500)


class HintResponse(BaseModel):
    """Güvenlik kapısı akışı durdurursa `hint` boş, `safety` dolu döner."""

    hint: HintOut | None
    can_request_next: bool
    notice: str | None = None
    safety: SafetyNotice | None = None


class AttemptRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=200)


class AttemptResponse(BaseModel):
    """Cevap kontrolü. Doğru cevap yanlış denemelerde bilerek açıklanmaz."""

    correct: bool | None
    solved: bool
    feedback: str
    hint: HintOut | None
    can_request_next: bool
    safety: SafetyNotice | None = None


class HintFeedbackRequest(BaseModel):
    helpful: bool


class HintFeedbackResponse(BaseModel):
    id: uuid.UUID
    helpful: bool


def _hint_out(hint: Hint) -> HintOut:
    return HintOut(
        id=hint.id, level=hint.level, level_name=ladder.LEVEL_NAMES[hint.level], text=hint.content
    )


def _can_request_next(state: str, current: int | None, problem_status: str) -> bool:
    if state != "open":
        return False
    return current is None or current < ladder.max_level_for(problem_status)


def _wants_sse(request: Request) -> bool:
    accept = request.headers.get("accept", "").lower()
    return "text/event-stream" in accept


async def _sse_hint_stream(payload: HintResponse) -> AsyncIterator[str]:
    """Yalnızca sızıntı + güvenlik kontrolünden GEÇMİŞ ipucunu SSE olaylarıyla akıtır (Kural 2)."""
    if payload.hint is not None:
        words = payload.hint.text.split(" ")
        step = 3
        for idx in range(0, len(words), step):
            piece = " ".join(words[idx : idx + step])
            if idx + step < len(words):
                piece += " "
            yield f"event: delta\ndata: {json.dumps({'text': piece}, ensure_ascii=False)}\n\n"
    body = payload.model_dump(mode="json")
    if payload.hint is not None:
        body.update(
            {
                "hint_id": str(payload.hint.id),
                "level": payload.hint.level,
                "level_name": payload.hint.level_name,
                "text": payload.hint.text,
            }
        )
    yield f"event: hint\ndata: {json.dumps(body, ensure_ascii=False)}\n\n"


@tutoring_router.get("/{problem_id}", response_model=ProblemDetail)
async def get_problem(problem_id: uuid.UUID, child: Child, db: Db) -> ProblemDetail:
    problem = await service.get_child_problem(db, child.id, problem_id)
    solution = await service.load_solution(db, problem)
    hints = await service.list_hints(db, problem.id)
    return ProblemDetail(
        id=problem.id,
        text=problem.masked_text,
        status=problem.status,
        topic=solution.topic if solution else None,
        state=problem.state,
        current_hint_level=problem.current_hint_level,
        max_hint_level=ladder.max_level_for(problem.status),
        can_request_hint=_can_request_next(
            problem.state, problem.current_hint_level, problem.status
        ),
        hints=[_hint_out(hint) for hint in hints],
        attempts_count=await service.count_attempts(db, problem.id),
    )


@tutoring_router.post("/{problem_id}/hints", response_model=HintResponse)
async def request_hint(
    problem_id: uuid.UUID,
    data: HintRequest,
    request: Request,
    child: Child,
    db: Db,
    gateway: Gateway,
) -> HintResponse | Response:
    problem = await service.get_child_problem(db, child.id, problem_id)
    screening = await screen_input(
        db, child_id=child.id, problem_id=problem.id, text=data.message, source="hint_message"
    )
    if screening.safety is not None:
        blocked = HintResponse(
            hint=None,
            can_request_next=_can_request_next(
                problem.state, problem.current_hint_level, problem.status
            ),
            safety=screening.safety,
        )
        if _wants_sse(request):
            return StreamingResponse(
                _sse_hint_stream(blocked),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        return blocked
    try:
        hint = await service.request_hint(db, child, problem_id, data.message, gateway)
    except ConsentRequiredError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _CONSENT_MESSAGE) from None
    except DailyLimitExceededError:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, _DAILY_LIMIT_MESSAGE) from None
    problem = await service.get_child_problem(db, child.id, problem_id)
    result = HintResponse(
        hint=_hint_out(hint),
        can_request_next=_can_request_next(problem.state, hint.level, problem.status),
        notice=screening.notice,
    )
    if _wants_sse(request):
        return StreamingResponse(
            _sse_hint_stream(result),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    return result


@tutoring_router.post("/{problem_id}/attempts", response_model=AttemptResponse)
async def submit_attempt(
    problem_id: uuid.UUID, data: AttemptRequest, child: Child, db: Db, gateway: Gateway
) -> AttemptResponse:
    problem = await service.get_child_problem(db, child.id, problem_id)
    screening = await screen_input(
        db, child_id=child.id, problem_id=problem.id, text=data.answer, source="attempt"
    )
    if screening.safety is not None:
        return AttemptResponse(
            correct=None,
            solved=False,
            feedback=screening.safety.message,
            hint=None,
            can_request_next=_can_request_next(
                problem.state, problem.current_hint_level, problem.status
            ),
            safety=screening.safety,
        )
    try:
        outcome = await service.submit_attempt(db, child, problem_id, data.answer, gateway)
    except ConsentRequiredError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _CONSENT_MESSAGE) from None
    except DailyLimitExceededError:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, _DAILY_LIMIT_MESSAGE) from None
    problem = await service.get_child_problem(db, child.id, problem_id)
    return AttemptResponse(
        correct=outcome.attempt.is_correct,
        solved=outcome.solved,
        feedback=outcome.feedback,
        hint=_hint_out(outcome.hint) if outcome.hint else None,
        can_request_next=_can_request_next(
            problem.state, problem.current_hint_level, problem.status
        ),
    )


@hints_router.post("/{hint_id}/feedback", response_model=HintFeedbackResponse)
async def submit_hint_feedback(
    hint_id: uuid.UUID, data: HintFeedbackRequest, child: Child, db: Db
) -> HintFeedbackResponse:
    hint = await service.set_hint_feedback(db, child.id, hint_id, data.helpful)
    return HintFeedbackResponse(id=hint.id, helpful=bool(hint.helpful))
