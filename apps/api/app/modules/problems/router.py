import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth_consent.deps import get_current_child
from app.modules.auth_consent.models import ChildProfile
from app.modules.llm_gateway.providers import (
    ConsentRequiredError,
    DailyLimitExceededError,
    LLMError,
)
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.problems.service import DailyProblemLimitExceededError, create_problem
from app.modules.safety.service import SafetyNotice, screen_input

problems_router = APIRouter(prefix="/v1/problems", tags=["problems"])


def get_llm_gateway() -> LLMGatewayService:
    return LLMGatewayService()


class ProblemCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ProblemResponse(BaseModel):
    """Öğrenciye dönen bilgi. Gizli çözüm, adımlar ve nihai cevap bilerek yoktur.

    Güvenlik kapısı akışı durdurursa soru oluşturulmaz: `id` boş, `status` 'blocked' olur ve
    `safety` sabit destek mesajını taşır (HTTP 200).
    """

    id: uuid.UUID | None
    status: str
    grade: int | None
    topic: str | None
    notice: str | None = None
    safety: SafetyNotice | None = None


@problems_router.post("", status_code=status.HTTP_201_CREATED, response_model=ProblemResponse)
async def submit_problem(
    data: ProblemCreateRequest,
    response: Response,
    child: Annotated[ChildProfile, Depends(get_current_child)],
    db: Annotated[AsyncSession, Depends(get_db)],
    gateway: Annotated[LLMGatewayService, Depends(get_llm_gateway)],
) -> ProblemResponse:
    text = data.text.strip()
    if not text:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Soru metni boş olamaz")
    # Adım 1: girdi güvenliği. Kriz/uygunsuz içerikte LLM çağrılmaz ve metin saklanmaz.
    screening = await screen_input(
        db, child_id=child.id, problem_id=None, text=text, source="problem"
    )
    if screening.safety is not None:
        response.status_code = status.HTTP_200_OK
        return ProblemResponse(
            id=None, status="blocked", grade=None, topic=None, safety=screening.safety
        )
    try:
        problem, solution = await create_problem(
            db, child.id, text, gateway, daily_limit=child.daily_new_problem_limit
        )
    except ConsentRequiredError:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Yapay zekâ ile işleme izni yok. Ebeveyninden bu izni vermesini iste.",
        ) from None
    except (DailyLimitExceededError, DailyProblemLimitExceededError):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Bugünlük yeni soru hakkın doldu, yarın devam edelim.",
        ) from None
    except LLMError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Şu an çözüm hazırlanamıyor, biraz sonra tekrar dene.",
        ) from None
    return ProblemResponse(
        id=problem.id,
        status=problem.status,
        grade=solution.grade if solution is not None else None,
        topic=solution.topic if solution is not None else None,
        notice=screening.notice,
    )
