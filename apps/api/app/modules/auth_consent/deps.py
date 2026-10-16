import uuid
from typing import Annotated, Any, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_token
from app.modules.auth_consent.models import ChildProfile, User
from app.modules.auth_consent.service import has_service_consent

bearer_scheme = HTTPBearer(auto_error=False)


def _string_claim(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) else None


async def _require_access_user(
    credentials: HTTPAuthorizationCredentials | None, db: AsyncSession
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Kimlik doğrulama gerekli")
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Geçersiz belirteç") from None
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Geçersiz belirteç türü")
    sub = _string_claim(payload, "sub")
    if sub is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Geçersiz belirteç")
    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Geçersiz belirteç") from None
    user = cast(User | None, await db.get(User, user_id))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Kullanıcı bulunamadı")
    return user


async def get_current_guardian(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await _require_access_user(credentials, db)
    if user.role != "guardian":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Yalnızca ebeveyn")
    return user


async def get_current_child(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildProfile:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Kimlik doğrulama gerekli")
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Geçersiz belirteç") from None
    if payload.get("type") != "access" or payload.get("role") != "child":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Geçersiz çocuk belirteci")
    sub = _string_claim(payload, "sub")
    if sub is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Geçersiz belirteç")
    try:
        child_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Geçersiz belirteç") from None
    child = cast(ChildProfile | None, await db.get(ChildProfile, child_id))
    if child is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Çocuk profili bulunamadı")
    if not await has_service_consent(db, child.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Hizmet rızası yok")
    return child
