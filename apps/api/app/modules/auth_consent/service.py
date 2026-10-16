import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_pairing_code,
    hash_password,
    hash_refresh_token,
    new_pairing_code,
    new_refresh_token,
    verify_password,
)
from app.modules.auth_consent import models, schemas

PAIRING_CODE_TTL_MINUTES = 10
PAIRING_MAX_ATTEMPTS = 5


async def register_user(db: AsyncSession, data: schemas.RegisterRequest) -> models.User:
    email = data.email.lower()
    existing = cast(
        models.User | None, await db.scalar(select(models.User).where(models.User.email == email))
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu e-posta zaten kayıtlı")
    user = models.User(
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
        full_name=data.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> models.User | None:
    user = cast(
        models.User | None,
        await db.scalar(select(models.User).where(models.User.email == email.lower())),
    )
    if user is None or user.password_hash is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def issue_tokens(db: AsyncSession, user: models.User) -> schemas.TokenResponse:
    access = create_access_token(str(user.id), user.role, settings.access_token_ttl_minutes)
    raw_refresh = new_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days)
    db.add(
        models.RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=expires_at,
        )
    )
    await db.commit()
    return schemas.TokenResponse(access_token=access, refresh_token=raw_refresh)


async def rotate_refresh_token(db: AsyncSession, raw_refresh: str) -> schemas.TokenResponse:
    now = datetime.now(UTC)
    row = cast(
        models.RefreshToken | None,
        await db.scalar(
            select(models.RefreshToken).where(
                models.RefreshToken.token_hash == hash_refresh_token(raw_refresh)
            )
        ),
    )
    if row is None or row.revoked_at is not None or row.expires_at <= now:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Geçersiz veya süresi dolmuş yenileme belirteci"
        )
    user = cast(models.User | None, await db.get(models.User, row.user_id))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Kullanıcı bulunamadı")
    row.revoked_at = now
    access = create_access_token(str(user.id), user.role, settings.access_token_ttl_minutes)
    new_raw = new_refresh_token()
    new_expires = now + timedelta(days=settings.refresh_token_ttl_days)
    db.add(
        models.RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(new_raw),
            expires_at=new_expires,
        )
    )
    await db.commit()
    return schemas.TokenResponse(access_token=access, refresh_token=new_raw)


async def revoke_refresh_token(db: AsyncSession, raw_refresh: str) -> None:
    row = cast(
        models.RefreshToken | None,
        await db.scalar(
            select(models.RefreshToken).where(
                models.RefreshToken.token_hash == hash_refresh_token(raw_refresh)
            )
        ),
    )
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
        await db.commit()


def age_band_for(birth_year: int) -> str | None:
    age = datetime.now(UTC).year - birth_year
    if 7 <= age <= 10:
        return "7-10"
    if 11 <= age <= 13:
        return "11-13"
    if 14 <= age <= 17:
        return "14-17"
    return None


async def create_child(
    db: AsyncSession, guardian: models.User, data: schemas.ChildCreateRequest
) -> models.ChildProfile:
    band = age_band_for(data.birth_year)
    if band is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Doğum yılı 7-17 yaş aralığında olmalı"
        )
    child = models.ChildProfile(
        guardian_id=guardian.id,
        nickname=data.nickname,
        birth_year=data.birth_year,
        grade=data.grade,
        age_band=band,
    )
    db.add(child)
    await db.flush()
    for purpose in data.purposes:
        db.add(
            models.Consent(
                child_id=child.id,
                guardian_id=guardian.id,
                purpose=purpose,
                policy_version="v0-draft",
                granted=True,
                evidence={},
            )
        )
    await db.commit()
    await db.refresh(child)
    return child


async def get_owned_child(
    db: AsyncSession, guardian: models.User, child_id: uuid.UUID
) -> models.ChildProfile:
    child = cast(models.ChildProfile | None, await db.get(models.ChildProfile, child_id))
    if child is None or child.guardian_id != guardian.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Çocuk profili bulunamadı")
    return child


async def update_child(
    db: AsyncSession,
    guardian: models.User,
    child_id: uuid.UUID,
    data: schemas.ChildPatchRequest,
) -> models.ChildProfile:
    child = await get_owned_child(db, guardian, child_id)
    if data.nickname is not None:
        child.nickname = data.nickname
    if data.daily_new_problem_limit is not None:
        child.daily_new_problem_limit = data.daily_new_problem_limit
    if data.solution_policy is not None:
        child.solution_policy = data.solution_policy
    if data.privacy_level is not None:
        child.privacy_level = data.privacy_level
    await db.commit()
    await db.refresh(child)
    return child


async def set_consents(
    db: AsyncSession, guardian: models.User, child_id: uuid.UUID, data: schemas.ConsentRequest
) -> None:
    child = await get_owned_child(db, guardian, child_id)
    now = datetime.now(UTC)
    for purpose in data.purposes:
        existing = cast(
            models.Consent | None,
            await db.scalar(
                select(models.Consent).where(
                    models.Consent.child_id == child.id, models.Consent.purpose == purpose
                )
            ),
        )
        if existing is None:
            db.add(
                models.Consent(
                    child_id=child.id,
                    guardian_id=guardian.id,
                    purpose=purpose,
                    policy_version="v0-draft",
                    granted=data.grant,
                    granted_at=now,
                    revoked_at=None if data.grant else now,
                    evidence={},
                )
            )
        else:
            existing.granted = data.grant
            existing.revoked_at = None if data.grant else now
    await db.commit()


async def has_service_consent(db: AsyncSession, child_id: uuid.UUID) -> bool:
    row = await db.scalar(
        select(models.Consent).where(
            models.Consent.child_id == child_id,
            models.Consent.purpose == "service",
            models.Consent.granted.is_(True),
            models.Consent.revoked_at.is_(None),
        )
    )
    return row is not None


async def create_pairing_code(
    db: AsyncSession, guardian: models.User, child_id: uuid.UUID
) -> schemas.PairingCodeResponse:
    child = await get_owned_child(db, guardian, child_id)
    if not await has_service_consent(db, child.id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Hizmet rızası olmadan eşleştirme kodu üretilemez"
        )
    code = new_pairing_code()
    expires_at = datetime.now(UTC) + timedelta(minutes=PAIRING_CODE_TTL_MINUTES)
    row = models.PairingCode(
        child_id=child.id,
        code_hash=hash_pairing_code(code),
        expires_at=expires_at,
        max_attempts=PAIRING_MAX_ATTEMPTS,
        created_by=guardian.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return schemas.PairingCodeResponse(code=code, expires_at=row.expires_at)


async def redeem_pairing_code(
    db: AsyncSession, child_id: uuid.UUID, code: str
) -> models.ChildProfile:
    now = datetime.now(UTC)
    row = cast(
        models.PairingCode | None,
        await db.scalar(
            select(models.PairingCode)
            .where(models.PairingCode.child_id == child_id)
            .order_by(models.PairingCode.created_at.desc())
            .limit(1)
        ),
    )
    if row is None or row.used_at is not None or row.expires_at <= now:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Geçersiz veya süresi dolmuş kod")
    if row.attempts >= row.max_attempts:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Çok fazla hatalı deneme")
    if row.code_hash != hash_pairing_code(code):
        row.attempts += 1
        await db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Geçersiz kod")
    child = cast(models.ChildProfile | None, await db.get(models.ChildProfile, row.child_id))
    if child is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Çocuk profili bulunamadı")
    if not await has_service_consent(db, child.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Hizmet rızası yok")
    row.used_at = now
    await db.commit()
    return child
