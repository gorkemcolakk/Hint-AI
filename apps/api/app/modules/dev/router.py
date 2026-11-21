"""Yerel deneme kısayolları: eşleştirme bağlantısı üretmeden demo oturumu açar.

Bu router yalnızca HINT_DEV_SHORTCUTS=true iken uygulamaya eklenir (varsayılan kapalı) ve
OpenAPI şemasında görünmez. Kimlik doğrulamasını atladığı için canlı ortamda ASLA açılmamalıdır.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token
from app.modules.auth_consent import schemas
from app.modules.auth_consent.service import issue_tokens
from app.modules.dev.demo import ensure_demo_classroom, ensure_demo_family

dev_router = APIRouter(prefix="/v1/dev", tags=["dev"], include_in_schema=False)

Db = Annotated[AsyncSession, Depends(get_db)]


@dev_router.post("/demo-child", response_model=schemas.ChildTokenResponse)
async def demo_child(db: Db) -> schemas.ChildTokenResponse:
    _, child = await ensure_demo_family(db)
    access = create_access_token(str(child.id), "child", settings.child_token_ttl_minutes)
    return schemas.ChildTokenResponse(access_token=access)


@dev_router.post("/demo-guardian", response_model=schemas.TokenResponse)
async def demo_guardian(db: Db) -> schemas.TokenResponse:
    guardian, _ = await ensure_demo_family(db)
    return await issue_tokens(db, guardian)


@dev_router.post("/demo-teacher", response_model=schemas.TokenResponse)
async def demo_teacher(db: Db) -> schemas.TokenResponse:
    teacher, _ = await ensure_demo_classroom(db)
    return await issue_tokens(db, teacher)
