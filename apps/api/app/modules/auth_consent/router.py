import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token
from app.modules.auth_consent import schemas
from app.modules.auth_consent.deps import get_current_child, get_current_guardian
from app.modules.auth_consent.models import ChildProfile, User
from app.modules.auth_consent.service import (
    authenticate_user,
    create_child,
    create_pairing_code,
    get_owned_child,
    issue_tokens,
    list_owned_children,
    redeem_pairing_code,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
    set_consents,
    update_child,
)

auth_router = APIRouter(prefix="/v1/auth", tags=["auth"])
children_router = APIRouter(prefix="/v1/children", tags=["children"])

Db = Annotated[AsyncSession, Depends(get_db)]
Guardian = Annotated[User, Depends(get_current_guardian)]


def _to_child_response(child: ChildProfile) -> schemas.ChildProfileResponse:
    return schemas.ChildProfileResponse(
        id=child.id,
        nickname=child.nickname,
        birth_year=child.birth_year,
        grade=child.grade,
        age_band=child.age_band,
        daily_new_problem_limit=child.daily_new_problem_limit,
        solution_policy=child.solution_policy,
        privacy_level=child.privacy_level,
    )


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: schemas.RegisterRequest, db: Db) -> dict[str, str]:
    user = await register_user(db, data)
    return {"id": str(user.id), "email": user.email, "role": user.role}


@auth_router.post("/login", response_model=schemas.TokenResponse)
async def login(data: schemas.LoginRequest, db: Db) -> schemas.TokenResponse:
    user = await authenticate_user(db, data.email, data.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-posta veya parola hatalı")
    return await issue_tokens(db, user)


@auth_router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh(data: schemas.RefreshRequest, db: Db) -> schemas.TokenResponse:
    return await rotate_refresh_token(db, data.refresh_token)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(data: schemas.LogoutRequest, db: Db) -> None:
    await revoke_refresh_token(db, data.refresh_token)


@auth_router.post("/verify-email")
async def verify_email() -> dict[str, str]:
    # M1: e-posta gönderilmez (stub); log'a yazılmaz. TODO: gerçek sağlayıcı entegrasyonu.
    return {"status": "stub"}


@auth_router.post("/child-pair", response_model=schemas.ChildTokenResponse)
async def child_pair(data: schemas.ChildPairRequest, db: Db) -> schemas.ChildTokenResponse:
    child = await redeem_pairing_code(db, data.child_id, data.code)
    access = create_access_token(str(child.id), "child", settings.child_token_ttl_minutes)
    return schemas.ChildTokenResponse(access_token=access)


@children_router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=schemas.ChildProfileResponse
)
async def create_child_endpoint(
    data: schemas.ChildCreateRequest, guardian: Guardian, db: Db
) -> schemas.ChildProfileResponse:
    child = await create_child(db, guardian, data)
    return _to_child_response(child)


@children_router.get("", response_model=list[schemas.ChildProfileResponse])
async def list_children(guardian: Guardian, db: Db) -> list[schemas.ChildProfileResponse]:
    children = await list_owned_children(db, guardian)
    return [_to_child_response(child) for child in children]


@children_router.get("/me", response_model=schemas.ChildProfileResponse)
async def child_me(
    child: Annotated[ChildProfile, Depends(get_current_child)],
) -> schemas.ChildProfileResponse:
    return _to_child_response(child)


@children_router.get("/{child_id}", response_model=schemas.ChildProfileResponse)
async def get_child(
    child_id: uuid.UUID, guardian: Guardian, db: Db
) -> schemas.ChildProfileResponse:
    child = await get_owned_child(db, guardian, child_id)
    return _to_child_response(child)


@children_router.patch("/{child_id}", response_model=schemas.ChildProfileResponse)
async def patch_child(
    child_id: uuid.UUID, data: schemas.ChildPatchRequest, guardian: Guardian, db: Db
) -> schemas.ChildProfileResponse:
    child = await update_child(db, guardian, child_id, data)
    return _to_child_response(child)


@children_router.post("/{child_id}/consents", status_code=status.HTTP_204_NO_CONTENT)
async def grant_consents(
    child_id: uuid.UUID, data: schemas.ConsentRequest, guardian: Guardian, db: Db
) -> None:
    await set_consents(db, guardian, child_id, data)


@children_router.post("/{child_id}/device-pairing", response_model=schemas.PairingCodeResponse)
async def device_pairing(
    child_id: uuid.UUID, guardian: Guardian, db: Db
) -> schemas.PairingCodeResponse:
    return await create_pairing_code(db, guardian, child_id)
