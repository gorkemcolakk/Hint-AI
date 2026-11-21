"""İpucu ve deneme kayıtları.

İpucu metni yalnızca maskeli soru ve gizli çözümden üretilir ve sızıntı kontrolünden geçmiştir.
Öğrencinin cevabı PII maskelenmiş haliyle saklanır.
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


class Hint(Base):
    __tablename__ = "hints"
    __table_args__ = (
        CheckConstraint("level BETWEEN 0 AND 5", name="ck_hints_level"),
        CheckConstraint("source IN ('llm','fallback')", name="ck_hints_source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    level: Mapped[int] = mapped_column(SmallInteger)
    content: Mapped[str] = mapped_column(Text)
    # 'llm': model üretti ve sızıntı kontrolünü geçti; 'fallback': hazır güvenli ipucu.
    source: Mapped[str] = mapped_column(String(20))
    # {rule_pass, generations, reasons, judge}; ipucu metni veya cevap içermez.
    leak_check: Mapped[dict[str, object]] = mapped_column(JSONB)
    prompt_version: Mapped[str | None] = mapped_column(String(50))
    llm_call_id: Mapped[uuid.UUID | None] = mapped_column()
    helpful: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), index=True
    )
    answer_masked: Mapped[str] = mapped_column(Text)
    # None: cevap matematiksel olarak okunamadı ya da karşılaştırılacak çözüm yok.
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
