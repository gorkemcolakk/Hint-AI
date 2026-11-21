"""Soru ve gizli çözüm veri modeli.

Soru metni yalnızca PII maskelenmiş haliyle saklanır. Gizli çözüm öğrenciye asla
gösterilmez; ipucu üretimi (M4) için kaynak olarak kullanılır.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.auth_consent.models import Base

PROBLEM_STATUSES = ("verified", "low_confidence", "unverifiable", "failed")
# Öğretim durumu (status'tan ayrı: status çözümün doğrulama durumudur).
PROBLEM_STATES = ("open", "solved")


class HiddenSolution(Base):
    """Normalleştirilmiş soru → çözüm. Öğrenci verisi içermez, sorular arasında önbellektir."""

    __tablename__ = "hidden_solutions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    problem_hash: Mapped[str] = mapped_column(String(64), index=True)
    grade: Mapped[int | None] = mapped_column(SmallInteger)
    topic: Mapped[str | None] = mapped_column(String(120))
    steps: Mapped[list[str]] = mapped_column(JSONB)
    final_answer: Mapped[str] = mapped_column(Text)
    sympy_check: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    verified: Mapped[bool] = mapped_column(Boolean)
    verification_note: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Problem(Base):
    __tablename__ = "problems"
    __table_args__ = (
        CheckConstraint(
            "status IN ('verified','low_confidence','unverifiable','failed')",
            name="ck_problems_status",
        ),
        CheckConstraint("state IN ('open','solved')", name="ck_problems_state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE"), index=True
    )
    masked_text: Mapped[str] = mapped_column(Text)
    problem_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20))
    solution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("hidden_solutions.id", ondelete="SET NULL")
    )
    state: Mapped[str] = mapped_column(String(20), default="open", server_default="open")
    # Son verilen ipucunun seviyesi; henüz ipucu verilmediyse None.
    current_hint_level: Mapped[int | None] = mapped_column(SmallInteger)
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
