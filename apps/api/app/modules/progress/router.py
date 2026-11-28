import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth_consent.deps import get_current_guardian
from app.modules.auth_consent.models import User
from app.modules.auth_consent.service import get_owned_child
from app.modules.progress.service import (
    ChildDataExport,
    ChildSummary,
    build_child_export,
    build_summary,
)

progress_router = APIRouter(prefix="/v1/children", tags=["progress"])


@progress_router.get("/{child_id}/summary", response_model=ChildSummary)
async def child_summary(
    child_id: uuid.UUID,
    guardian: Annotated[User, Depends(get_current_guardian)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=90)] = 7,
) -> ChildSummary:
    """Ebeveynin kendi çocuğu için dönem özeti (başka ebeveynin çocuğu 404)."""
    child = await get_owned_child(db, guardian, child_id)
    return await build_summary(db, child, days)


@progress_router.get("/{child_id}/export", response_model=ChildDataExport)
async def export_child_data(
    child_id: uuid.UUID,
    guardian: Annotated[User, Depends(get_current_guardian)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildDataExport:
    """Ebeveynin kendi çocuğuna ait KVKK veri taşınabilirliği paketi."""
    child = await get_owned_child(db, guardian, child_id)
    return await build_child_export(db, child)
