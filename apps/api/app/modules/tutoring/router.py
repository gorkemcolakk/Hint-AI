import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth_consent.deps import get_current_child
from app.modules.auth_consent.models import ChildProfile
from app.modules.llm_gateway.providers import ConsentRequiredError
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.problems.router import get_llm_gateway
from app.modules.safety.service import SafetyNotice, screen_input
from app.modules.tutoring import ladder, service
from app.modules.tutoring.models import Hint

tutoring_router = APIRouter(prefix="/v1/problems", tags=["tutoring"])

Child = Annotated[ChildProfile, Depends(get_current_child)]
Db = Annotated[AsyncSession, Depends(get_db)]
Gateway = Annotated[LLMGatewayService, Depends(get_llm_gateway)]

_CONSENT_MESSAGE = "Yapay zekâ ile işleme izni yok. Ebeveyninden bu izni vermesini iste."


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


def _hint_out(hint: Hint) -> HintOut:
    return HintOut(
        id=hint.id, level=hint.level, level_name=ladder.LEVEL_NAMES[hint.level], text=hint.content
    )


def _can_request_next(state: str, current: int | None, problem_status: str) -> bool:
    if state != "open":
        return False
    return current is None or current < ladder.max_level_for(problem_status)


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
    problem_id: uuid.UUID, data: HintRequest, child: Child, db: Db, gateway: Gateway
) -> HintResponse:
    problem = await service.get_child_problem(db, child.id, problem_id)
    screening = await screen_input(
        db, child_id=child.id, problem_id=problem.id, text=data.message, source="hint_message"
    )
    if screening.safety is not None:
        return HintResponse(
            hint=None,
            can_request_next=_can_request_next(
                problem.state, problem.current_hint_level, problem.status
            ),
            safety=screening.safety,
        )
    try:
        hint = await service.request_hint(db, child, problem_id, data.message, gateway)
    except ConsentRequiredError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, _CONSENT_MESSAGE) from None
    problem = await service.get_child_problem(db, child.id, problem_id)
    return HintResponse(
        hint=_hint_out(hint),
        can_request_next=_can_request_next(problem.state, hint.level, problem.status),
        notice=screening.notice,
    )


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
