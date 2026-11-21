import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth_consent.deps import get_current_guardian, get_current_teacher
from app.modules.auth_consent.models import User
from app.modules.auth_consent.service import get_owned_child
from app.modules.classrooms import service
from app.modules.classrooms.service import (
    ChildClassroom,
    ClassroomOut,
    ClassroomPreview,
    Heatmap,
)

classrooms_router = APIRouter(prefix="/v1/classrooms", tags=["classrooms"])
child_classrooms_router = APIRouter(prefix="/v1/children", tags=["classrooms"])

Db = Annotated[AsyncSession, Depends(get_db)]
Teacher = Annotated[User, Depends(get_current_teacher)]
Guardian = Annotated[User, Depends(get_current_guardian)]


class ClassroomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    grade: int | None = Field(default=None, ge=1, le=12)


class JoinCodeRequest(BaseModel):
    code: str = Field(min_length=4, max_length=20)


# --- Öğretmen -----------------------------------------------------------------------------


@classrooms_router.post("", status_code=status.HTTP_201_CREATED, response_model=ClassroomOut)
async def create_classroom(data: ClassroomCreate, teacher: Teacher, db: Db) -> ClassroomOut:
    classroom = await service.create_classroom(db, teacher, data.name.strip(), data.grade)
    return await service.classroom_out(db, classroom)


@classrooms_router.get("", response_model=list[ClassroomOut])
async def list_classrooms(teacher: Teacher, db: Db) -> list[ClassroomOut]:
    return [await service.classroom_out(db, c) for c in await service.list_classrooms(db, teacher)]


@classrooms_router.get("/{classroom_id}/heatmap", response_model=Heatmap)
async def heatmap(
    classroom_id: uuid.UUID,
    teacher: Teacher,
    db: Db,
    days: Annotated[int, Query(ge=1, le=180)] = 30,
) -> Heatmap:
    classroom = await service.get_teacher_classroom(db, teacher, classroom_id)
    return await service.build_heatmap(db, classroom, days)


# --- Ebeveyn: davet koduyla onay ------------------------------------------------------------


@classrooms_router.post("/preview", response_model=ClassroomPreview)
async def preview_classroom(data: JoinCodeRequest, guardian: Guardian, db: Db) -> ClassroomPreview:
    """Katılmadan önce: sınıf ve öğretmen adı, öğretmenin neleri göreceği."""
    classroom, teacher = await service.find_by_code(db, data.code)
    return service.preview(classroom, teacher)


@child_classrooms_router.get("/{child_id}/classrooms", response_model=list[ChildClassroom])
async def list_child_classrooms(
    child_id: uuid.UUID, guardian: Guardian, db: Db
) -> list[ChildClassroom]:
    child = await get_owned_child(db, guardian, child_id)
    return await service.child_classrooms(db, child)


@child_classrooms_router.post(
    "/{child_id}/classrooms", status_code=status.HTTP_201_CREATED, response_model=ChildClassroom
)
async def join_classroom(
    child_id: uuid.UUID, data: JoinCodeRequest, guardian: Guardian, db: Db
) -> ChildClassroom:
    """Ebeveynin bu çağrıyı yapması, öğretmenin özet veriyi görmesine açık onaydır."""
    child = await get_owned_child(db, guardian, child_id)
    return await service.join_classroom(db, guardian, child, data.code)


@child_classrooms_router.delete(
    "/{child_id}/classrooms/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def leave_classroom(
    child_id: uuid.UUID, classroom_id: uuid.UUID, guardian: Guardian, db: Db
) -> None:
    """Onayı geri çekme: öğretmen bu çocuğun verisini artık göremez."""
    child = await get_owned_child(db, guardian, child_id)
    await service.leave_classroom(db, child, classroom_id)
