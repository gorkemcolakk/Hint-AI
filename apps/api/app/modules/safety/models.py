"""Güvenlik olayları. Çocuğun metni SAKLANMAZ; yalnızca kategori, aşama ve alınan eylem."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.auth_consent.models import Base


class ModerationEvent(Base):
    __tablename__ = "moderation_events"
    __table_args__ = (CheckConstraint("stage IN ('input','output')", name="ck_moderation_stage"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"), index=True
    )
    problem_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("problems.id", ondelete="SET NULL")
    )
    stage: Mapped[str] = mapped_column(String(10))
    # problem | hint_message | attempt | hint_output
    source: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(30), index=True)
    severity: Mapped[int] = mapped_column(SmallInteger)
    # blocked | redirected | noticed | regenerated; kriz olayları ebeveyne bildirilmek üzere
    # işaretlenir.
    action: Mapped[str] = mapped_column(String(20))
    notify_guardian: Mapped[bool] = mapped_column(default=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column()
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


async def record_event(
    db: AsyncSession,
    *,
    child_id: uuid.UUID,
    problem_id: uuid.UUID | None,
    stage: str,
    source: str,
    category: str,
    severity: int,
    action: str,
) -> None:
    """Olayı oturuma ekler (commit çağıranın işidir)."""
    db.add(
        ModerationEvent(
            child_id=child_id,
            problem_id=problem_id,
            stage=stage,
            source=source,
            category=category,
            severity=severity,
            action=action,
            notify_guardian=guardian_should_see(category, severity),
        )
    )


# İstismar bildiriminde zarar veren kişi ebeveyn olabilir; bu olaylar ebeveyne GÖSTERİLMEZ,
# yalnızca insan incelemesine (moderatör) gider. ⚠️ Nihai politika hukuk/uzman ile belirlenmeli
# (Bölüm 10.2).
GUARDIAN_HIDDEN_CATEGORIES = frozenset({"abuse_disclosure"})


def guardian_should_see(category: str, severity: int) -> bool:
    return severity >= 3 and category not in GUARDIAN_HIDDEN_CATEGORIES
