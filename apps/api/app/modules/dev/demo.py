"""Yerel demo verisi (tamamı SAHTE): demo ebeveyn + çocuk, demo öğretmen + sınıf.

Sınıfın ısı haritası tek çocukla anlamsız olacağı için ayrı bir sentetik ebeveyne bağlı birkaç
sentetik öğrenci ve sentetik çalışma kayıtları üretilir. Gerçek kullanıcı verisi değildir.
"""

from datetime import UTC, datetime
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth_consent import models, schemas
from app.modules.auth_consent.service import create_child, register_user
from app.modules.classrooms.models import Classroom, Enrollment
from app.modules.classrooms.service import create_classroom
from app.modules.problems.models import HiddenSolution, Problem
from app.modules.tutoring.models import Hint

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo12345"
DEMO_CHILD_NICKNAME = "Deniz"
DEMO_CHILD_GRADE = 6

DEMO_TEACHER_EMAIL = "ogretmen@example.com"
DEMO_CLASS_NAME = "6-A Matematik"
DEMO_CLASS_CODE = "DEMO6A"
SYNTHETIC_GUARDIAN_EMAIL = "sentetik@example.com"

# Sentetik öğrenci → konu → (soru, çözülen, soru başına ipucu)
SYNTHETIC_STUDY: dict[str, dict[str, tuple[int, int, int]]] = {
    "Ali": {
        "kesirlerle toplama": (4, 4, 1),
        "birinci dereceden denklem": (3, 2, 3),
        "yüzdeler": (2, 1, 4),
    },
    "Zeynep": {
        "kesirlerle toplama": (5, 5, 0),
        "birinci dereceden denklem": (4, 4, 1),
        "alan ve çevre": (2, 2, 1),
    },
    "Mert": {
        "kesirlerle toplama": (3, 2, 2),
        "yüzdeler": (3, 0, 5),
        "alan ve çevre": (2, 1, 3),
    },
    "Elif": {
        "birinci dereceden denklem": (5, 3, 3),
        "yüzdeler": (2, 1, 4),
        "alan ve çevre": (3, 3, 0),
    },
}


async def _ensure_user(db: AsyncSession, email: str, role: str, full_name: str) -> models.User:
    user = cast(
        models.User | None,
        await db.scalar(select(models.User).where(models.User.email == email)),
    )
    if user is None:
        user = await register_user(
            db,
            schemas.RegisterRequest(
                email=email,
                password=DEMO_PASSWORD,
                role=role,
                full_name=full_name,
            ),
        )
    return user


async def _ensure_child(
    db: AsyncSession, guardian: models.User, nickname: str
) -> models.ChildProfile:
    child = cast(
        models.ChildProfile | None,
        await db.scalar(
            select(models.ChildProfile).where(
                models.ChildProfile.guardian_id == guardian.id,
                models.ChildProfile.nickname == nickname,
            )
        ),
    )
    if child is None:
        child = await create_child(
            db,
            guardian,
            schemas.ChildCreateRequest(
                nickname=nickname,
                birth_year=datetime.now(UTC).year - 11,
                grade=DEMO_CHILD_GRADE,
                purposes=["service", "llm_processing"],
            ),
        )
    return child


async def ensure_demo_family(db: AsyncSession) -> tuple[models.User, models.ChildProfile]:
    """Demo ebeveyni ve çocuğu yoksa oluşturur, varsa olanları döner."""
    guardian = await _ensure_user(db, DEMO_EMAIL, "guardian", "Demo Ebeveyn")
    child = await _ensure_child(db, guardian, DEMO_CHILD_NICKNAME)
    if child.daily_new_problem_limit < 25:
        child.daily_new_problem_limit = 50
        await db.commit()
        await db.refresh(child)
    return guardian, child


def _approve(classroom: Classroom, child: models.ChildProfile, guardian: models.User) -> Enrollment:
    return Enrollment(
        classroom_id=classroom.id,
        child_id=child.id,
        guardian_approved=True,
        approved_by=guardian.id,
        approved_at=datetime.now(UTC),
    )


async def _seed_study(db: AsyncSession, child: models.ChildProfile, nickname: str) -> None:
    for topic, (problems, solved, hints) in SYNTHETIC_STUDY[nickname].items():
        solution = HiddenSolution(
            problem_hash=f"sentetik-{nickname}-{topic}"[:64],
            topic=topic,
            steps=["sentetik"],
            final_answer="1",
            verified=True,
            prompt_version="sentetik",
            model="sentetik",
        )
        db.add(solution)
        await db.flush()
        for index in range(problems):
            problem = Problem(
                child_id=child.id,
                masked_text="Sentetik demo sorusu",
                problem_hash=solution.problem_hash,
                status="verified",
                solution_id=solution.id,
                state="solved" if index < solved else "open",
                current_hint_level=hints - 1 if hints else None,
            )
            db.add(problem)
            await db.flush()
            for level in range(hints):
                db.add(
                    Hint(
                        problem_id=problem.id,
                        level=level,
                        content="sentetik",
                        source="fallback",
                        leak_check={"synthetic": True},
                    )
                )


async def ensure_demo_classroom(db: AsyncSession) -> tuple[models.User, Classroom]:
    """Demo öğretmeni ve sınıfını hazırlar; ilk seferde demo çocuğu ve sentetik öğrencileri
    (ebeveyn onaylı olarak) kaydeder."""
    teacher = await _ensure_user(db, DEMO_TEACHER_EMAIL, "teacher", "Murat Öğretmen")
    classroom = cast(
        Classroom | None,
        await db.scalar(select(Classroom).where(Classroom.join_code == DEMO_CLASS_CODE)),
    )
    if classroom is not None:
        return teacher, classroom

    classroom = await create_classroom(db, teacher, DEMO_CLASS_NAME, 6, code=DEMO_CLASS_CODE)
    guardian, child = await ensure_demo_family(db)
    db.add(_approve(classroom, child, guardian))
    synthetic_guardian = await _ensure_user(
        db, SYNTHETIC_GUARDIAN_EMAIL, "guardian", "Sentetik Ebeveyn"
    )
    for nickname in SYNTHETIC_STUDY:
        synthetic_child = await _ensure_child(db, synthetic_guardian, nickname)
        db.add(_approve(classroom, synthetic_child, synthetic_guardian))
        await _seed_study(db, synthetic_child, nickname)
    await db.commit()
    return teacher, classroom
