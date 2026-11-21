"""Girdi güvenlik kapısı: uç noktalar çocuğun metnini işlemeden önce buradan geçirir."""

import uuid
from dataclasses import dataclass

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.llm_gateway.mask import mask_pii
from app.modules.safety.classifier import SafetyVerdict, classify
from app.modules.safety.messages import INJECTION_NOTICE, PII_NOTICE, support_for
from app.modules.safety.models import record_event


class SupportResourceOut(BaseModel):
    name: str
    phone: str
    note: str


class SafetyNotice(BaseModel):
    """Akış durduğunda çocuğa gösterilen sabit mesaj ve yardım hatları."""

    category: str
    message: str
    resources: list[SupportResourceOut]


@dataclass(frozen=True)
class InputScreening:
    verdict: SafetyVerdict
    # Akış durduysa gösterilecek sabit mesaj; None ise devam edilir.
    safety: SafetyNotice | None
    # Akış devam ederken gösterilecek nazik not (injection, kişisel bilgi).
    notice: str | None


def _notice_for(verdict: SafetyVerdict) -> SafetyNotice:
    message, resources = support_for(verdict.category)
    return SafetyNotice(
        category=verdict.category,
        message=message,
        resources=[SupportResourceOut(name=r.name, phone=r.phone, note=r.note) for r in resources],
    )


async def screen_input(
    db: AsyncSession,
    *,
    child_id: uuid.UUID,
    problem_id: uuid.UUID | None,
    text: str | None,
    source: str,
) -> InputScreening:
    """Metni sınıflandırır, olayı kaydeder (metin saklanmaz) ve ne yapılacağını döner.

    Olay oturuma eklenir; akış duruyorsa burada commit edilir, devam ediyorsa çağıranın
    sonraki commit'iyle birlikte yazılır.
    """
    verdict = classify(text)
    if verdict.blocks:
        await record_event(
            db,
            child_id=child_id,
            problem_id=problem_id,
            stage="input",
            source=source,
            category=verdict.category,
            severity=verdict.severity,
            action="blocked" if verdict.action == "block_with_support" else "redirected",
        )
        await db.commit()
        return InputScreening(verdict, _notice_for(verdict), None)

    notice: str | None = None
    if verdict.category == "prompt_injection":
        notice = INJECTION_NOTICE
        await record_event(
            db,
            child_id=child_id,
            problem_id=problem_id,
            stage="input",
            source=source,
            category=verdict.category,
            severity=verdict.severity,
            action="noticed",
        )
    elif text and mask_pii(text).detected_types:
        notice = PII_NOTICE
        await record_event(
            db,
            child_id=child_id,
            problem_id=problem_id,
            stage="input",
            source=source,
            category="pii_share",
            severity=1,
            action="noticed",
        )
    return InputScreening(verdict, None, notice)
