"""Sınıf işlemleri ve kazanım ısı haritası.

Gizlilik (Bölüm 5.2, 10.3): öğretmen yalnızca ebeveynin onayladığı çocukları, yalnızca konu
bazında sayılarla görür. Soru metni, ipucu metni ve güvenlik uyarıları öğretmene GÖSTERİLMEZ.

Bilinen sınır: "konu" gizli çözüm modelinin ürettiği serbest metindir; MEB kazanım kodlarına
eşleme (Bölüm 6.5) henüz yok. Yazım farkları küçük harfe çevrilip birleştirilir.
"""

import secrets
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import cast

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth_consent.models import ChildProfile, User
from app.modules.classrooms.models import Classroom, Enrollment
from app.modules.problems.models import HiddenSolution, Problem
from app.modules.safety.models import ModerationEvent
from app.modules.tutoring.models import Hint

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # karışan 0/O, 1/I yok
CODE_LENGTH = 6
UNKNOWN_TOPIC = "konu belirlenemedi"
TEACHER_SEES = (
    "Öğretmen, çocuğunun yalnızca takma adını ve konu bazında kaç soru çalışıp kaçını, kaç "
    "ipucuyla çözdüğünü görür. Soru ve ipucu metinlerini, güvenlik uyarılarını göremez. "
    "İstediğin zaman sınıftan ayrılabilirsin."
)


class ClassroomOut(BaseModel):
    id: uuid.UUID
    name: str
    grade: int | None
    join_code: str
    student_count: int


class ClassroomPreview(BaseModel):
    """Ebeveynin katılmadan önce gördüğü bilgi."""

    id: uuid.UUID
    name: str
    grade: int | None
    teacher_name: str
    teacher_sees: str


class ChildClassroom(BaseModel):
    id: uuid.UUID
    name: str
    teacher_name: str


class HeatmapStudent(BaseModel):
    child_id: uuid.UUID
    nickname: str
    problems: int
    solved: int
    avg_hints: float | None
    answer_requests: int


class HeatmapTopic(BaseModel):
    topic: str
    problems: int
    solved: int
    avg_hints: float | None
    students: int
    # Bu konuda ortalama 3+ ipucu kullanan ya da hiç çözemeyen öğrenci sayısı.
    struggling: int


class HeatmapCell(BaseModel):
    topic: str
    child_id: uuid.UUID
    problems: int
    solved: int
    avg_hints: float


class Heatmap(BaseModel):
    classroom: ClassroomOut
    period_days: int
    max_hints: int
    students: list[HeatmapStudent]
    topics: list[HeatmapTopic]
    cells: list[HeatmapCell]


def _new_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def normalize_code(code: str) -> str:
    return "".join(code.split()).upper()


def _teacher_name(teacher: User) -> str:
    return teacher.full_name or "Öğretmen"


async def _student_count(db: AsyncSession, classroom_id: uuid.UUID) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(Enrollment)
        .where(Enrollment.classroom_id == classroom_id, Enrollment.guardian_approved.is_(True))
    )
    return int(count or 0)


async def classroom_out(db: AsyncSession, classroom: Classroom) -> ClassroomOut:
    return ClassroomOut(
        id=classroom.id,
        name=classroom.name,
        grade=classroom.grade,
        join_code=classroom.join_code,
        student_count=await _student_count(db, classroom.id),
    )


async def create_classroom(
    db: AsyncSession, teacher: User, name: str, grade: int | None, code: str | None = None
) -> Classroom:
    for _ in range(10):
        candidate = code or _new_code()
        exists = await db.scalar(select(Classroom.id).where(Classroom.join_code == candidate))
        if exists is None:
            classroom = Classroom(
                teacher_id=teacher.id, name=name, grade=grade, join_code=candidate
            )
            db.add(classroom)
            await db.commit()
            await db.refresh(classroom)
            return classroom
        if code is not None:
            break
    raise HTTPException(status.HTTP_409_CONFLICT, "Davet kodu üretilemedi, tekrar dene")


async def list_classrooms(db: AsyncSession, teacher: User) -> list[Classroom]:
    rows = await db.scalars(
        select(Classroom).where(Classroom.teacher_id == teacher.id).order_by(Classroom.created_at)
    )
    return list(rows)


async def get_teacher_classroom(
    db: AsyncSession, teacher: User, classroom_id: uuid.UUID
) -> Classroom:
    classroom = cast(Classroom | None, await db.get(Classroom, classroom_id))
    if classroom is None or classroom.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sınıf bulunamadı")
    return classroom


async def find_by_code(db: AsyncSession, code: str) -> tuple[Classroom, User]:
    row = (
        await db.execute(
            select(Classroom, User)
            .join(User, User.id == Classroom.teacher_id)
            .where(Classroom.join_code == normalize_code(code))
        )
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bu davet koduyla bir sınıf bulunamadı")
    return row[0], row[1]


def preview(classroom: Classroom, teacher: User) -> ClassroomPreview:
    return ClassroomPreview(
        id=classroom.id,
        name=classroom.name,
        grade=classroom.grade,
        teacher_name=_teacher_name(teacher),
        teacher_sees=TEACHER_SEES,
    )


async def join_classroom(
    db: AsyncSession, guardian: User, child: ChildProfile, code: str
) -> ChildClassroom:
    """Ebeveynin katılması = açık onay. Kayıt guardian_approved=True olarak oluşur."""
    classroom, teacher = await find_by_code(db, code)
    enrollment = cast(
        Enrollment | None,
        await db.get(Enrollment, {"classroom_id": classroom.id, "child_id": child.id}),
    )
    if enrollment is None:
        enrollment = Enrollment(classroom_id=classroom.id, child_id=child.id)
        db.add(enrollment)
    enrollment.guardian_approved = True
    enrollment.approved_by = guardian.id
    enrollment.approved_at = datetime.now(UTC)
    await db.commit()
    return ChildClassroom(id=classroom.id, name=classroom.name, teacher_name=_teacher_name(teacher))


async def leave_classroom(db: AsyncSession, child: ChildProfile, classroom_id: uuid.UUID) -> None:
    enrollment = await db.get(Enrollment, {"classroom_id": classroom_id, "child_id": child.id})
    if enrollment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Çocuk bu sınıfta değil")
    await db.delete(enrollment)
    await db.commit()


async def child_classrooms(db: AsyncSession, child: ChildProfile) -> list[ChildClassroom]:
    rows = await db.execute(
        select(Classroom, User)
        .join(Enrollment, Enrollment.classroom_id == Classroom.id)
        .join(User, User.id == Classroom.teacher_id)
        .where(Enrollment.child_id == child.id, Enrollment.guardian_approved.is_(True))
        .order_by(Classroom.name)
    )
    return [
        ChildClassroom(id=classroom.id, name=classroom.name, teacher_name=_teacher_name(teacher))
        for classroom, teacher in rows
    ]


def _avg(total: int, count: int) -> float | None:
    return round(total / count, 1) if count else None


async def build_heatmap(db: AsyncSession, classroom: Classroom, days: int) -> Heatmap:
    since = datetime.now(UTC) - timedelta(days=days)
    students = (
        await db.execute(
            select(ChildProfile.id, ChildProfile.nickname)
            .join(Enrollment, Enrollment.child_id == ChildProfile.id)
            .where(
                Enrollment.classroom_id == classroom.id,
                Enrollment.guardian_approved.is_(True),
            )
            .order_by(ChildProfile.nickname)
        )
    ).all()
    child_ids = [child_id for child_id, _ in students]

    rows: list[tuple[uuid.UUID, uuid.UUID, str, str | None]] = []
    hint_counts: dict[uuid.UUID, int] = {}
    injections: dict[uuid.UUID, int] = defaultdict(int)
    if child_ids:
        rows = [
            (pid, cid, state, topic)
            for pid, cid, state, topic in await db.execute(
                select(Problem.id, Problem.child_id, Problem.state, HiddenSolution.topic)
                .outerjoin(HiddenSolution, HiddenSolution.id == Problem.solution_id)
                .where(Problem.child_id.in_(child_ids), Problem.created_at >= since)
            )
        ]
        problem_ids = [pid for pid, _, _, _ in rows]
        if problem_ids:
            hint_counts = {
                pid: int(n)
                for pid, n in await db.execute(
                    select(Hint.problem_id, func.count(Hint.id))
                    .where(Hint.problem_id.in_(problem_ids))
                    .group_by(Hint.problem_id)
                )
            }
        for cid, n in await db.execute(
            select(ModerationEvent.child_id, func.count(ModerationEvent.id))
            .where(
                ModerationEvent.child_id.in_(child_ids),
                ModerationEvent.category == "prompt_injection",
                ModerationEvent.created_at >= since,
            )
            .group_by(ModerationEvent.child_id)
        ):
            injections[cid] = int(n)

    # (konu, çocuk) → [soru, çözülen, ipucu]
    cell_stats: dict[tuple[str, uuid.UUID], list[int]] = defaultdict(lambda: [0, 0, 0])
    for pid, cid, state, topic in rows:
        key = ((topic or UNKNOWN_TOPIC).strip().lower(), cid)
        stat = cell_stats[key]
        stat[0] += 1
        stat[1] += state == "solved"
        stat[2] += hint_counts.get(pid, 0)

    student_out = []
    for child_id, nickname in students:
        mine = [s for (_, cid), s in cell_stats.items() if cid == child_id]
        problems = sum(s[0] for s in mine)
        student_out.append(
            HeatmapStudent(
                child_id=child_id,
                nickname=nickname,
                problems=problems,
                solved=sum(s[1] for s in mine),
                avg_hints=_avg(sum(s[2] for s in mine), problems),
                answer_requests=injections[child_id],
            )
        )

    topic_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0, 0])
    for (topic, _), (problems, solved, hints) in cell_stats.items():
        stat = topic_stats[topic]
        stat[0] += problems
        stat[1] += solved
        stat[2] += hints
        stat[3] += 1
        stat[4] += hints / problems >= 3 or solved == 0
    topics = sorted(
        (
            HeatmapTopic(
                topic=topic,
                problems=s[0],
                solved=s[1],
                avg_hints=_avg(s[2], s[0]),
                students=s[3],
                struggling=s[4],
            )
            for topic, s in topic_stats.items()
        ),
        key=lambda t: (-(t.avg_hints or 0), t.topic),
    )
    cells = [
        HeatmapCell(
            topic=topic,
            child_id=cid,
            problems=s[0],
            solved=s[1],
            avg_hints=round(s[2] / s[0], 1),
        )
        for (topic, cid), s in cell_stats.items()
    ]
    return Heatmap(
        classroom=await classroom_out(db, classroom),
        period_days=days,
        max_hints=5,
        students=student_out,
        topics=topics,
        cells=cells,
    )
