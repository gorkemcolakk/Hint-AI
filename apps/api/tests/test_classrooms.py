"""Öğretmen sınıfları: davet kodu, ebeveyn onayı, ısı haritası ve gizlilik."""

import uuid

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.classrooms.models import Enrollment
from app.modules.dev.router import dev_router
from app.modules.problems.models import HiddenSolution, Problem
from app.modules.safety.models import record_event
from app.modules.tutoring.models import Hint

PASSWORD = "gizli-parola-123"


async def _login(
    client: httpx.AsyncClient, email: str, role: str, name: str | None = None
) -> dict[str, str]:
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": PASSWORD, "role": role, "full_name": name},
    )
    login = await client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def _child(client: httpx.AsyncClient, guardian: dict[str, str], nickname: str) -> str:
    response = await client.post(
        "/v1/children",
        json={"nickname": nickname, "birth_year": 2014, "grade": 6, "purposes": ["service"]},
        headers=guardian,
    )
    return str(response.json()["id"])


async def _study(
    db: AsyncSession, child_id: str, topic: str, *, problems: int, solved: int, hints: int
) -> None:
    solution = HiddenSolution(
        problem_hash=uuid.uuid4().hex,
        topic=topic,
        steps=["x"],
        final_answer="1",
        verified=True,
        prompt_version="t",
        model="t",
    )
    db.add(solution)
    await db.flush()
    for index in range(problems):
        problem = Problem(
            child_id=uuid.UUID(child_id),
            masked_text="GİZLİ SORU METNİ",
            problem_hash=solution.problem_hash,
            status="verified",
            solution_id=solution.id,
            state="solved" if index < solved else "open",
        )
        db.add(problem)
        await db.flush()
        for level in range(hints):
            db.add(
                Hint(
                    problem_id=problem.id,
                    level=level,
                    content="GİZLİ İPUCU",
                    source="llm",
                    leak_check={},
                )
            )
    await db.commit()


async def test_only_teachers_create_and_see_their_own_classrooms(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    teacher = await _login(client, "ogr-1@example.com", "teacher", "Murat Öğretmen")
    guardian = await _login(client, "veli-c1@example.com", "guardian")
    other_teacher = await _login(client, "ogr-2@example.com", "teacher")

    created = await client.post(
        "/v1/classrooms", json={"name": "6-A Matematik", "grade": 6}, headers=teacher
    )
    assert created.status_code == 201
    body = created.json()
    assert len(body["join_code"]) == 6 and body["student_count"] == 0
    assert (
        await client.post("/v1/classrooms", json={"name": "x"}, headers=guardian)
    ).status_code == 403
    listed = await client.get("/v1/classrooms", headers=teacher)
    assert [c["name"] for c in listed.json()] == ["6-A Matematik"]
    assert (await client.get("/v1/classrooms", headers=other_teacher)).json() == []
    foreign = await client.get(f"/v1/classrooms/{body['id']}/heatmap", headers=other_teacher)
    assert foreign.status_code == 404


async def test_guardian_previews_joins_and_leaves(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    teacher = await _login(client, "ogr-3@example.com", "teacher", "Ayşe Öğretmen")
    guardian = await _login(client, "veli-c2@example.com", "guardian")
    child_id = await _child(client, guardian, "Deniz")
    classroom = (await client.post("/v1/classrooms", json={"name": "7-B"}, headers=teacher)).json()
    code = classroom["join_code"]

    preview = await client.post(
        "/v1/classrooms/preview", json={"code": f" {code.lower()} "}, headers=guardian
    )
    assert preview.status_code == 200
    assert preview.json()["teacher_name"] == "Ayşe Öğretmen"
    assert "göremez" in preview.json()["teacher_sees"]
    bad = await client.post("/v1/classrooms/preview", json={"code": "YOKYOK"}, headers=guardian)
    assert bad.status_code == 404

    # Önizleme kayıt oluşturmaz; öğretmen henüz kimseyi görmez.
    heatmap = await client.get(f"/v1/classrooms/{classroom['id']}/heatmap", headers=teacher)
    assert heatmap.json()["students"] == []

    joined = await client.post(
        f"/v1/children/{child_id}/classrooms", json={"code": code}, headers=guardian
    )
    assert joined.status_code == 201
    mine = await client.get(f"/v1/children/{child_id}/classrooms", headers=guardian)
    assert [c["name"] for c in mine.json()] == ["7-B"]
    heatmap = await client.get(f"/v1/classrooms/{classroom['id']}/heatmap", headers=teacher)
    assert [s["nickname"] for s in heatmap.json()["students"]] == ["Deniz"]

    left = await client.delete(
        f"/v1/children/{child_id}/classrooms/{classroom['id']}", headers=guardian
    )
    assert left.status_code == 204
    heatmap = await client.get(f"/v1/classrooms/{classroom['id']}/heatmap", headers=teacher)
    assert heatmap.json()["students"] == []


async def test_guardian_cannot_enroll_someone_elses_child(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    teacher = await _login(client, "ogr-4@example.com", "teacher")
    owner = await _login(client, "veli-c3@example.com", "guardian")
    stranger = await _login(client, "veli-c4@example.com", "guardian")
    child_id = await _child(client, owner, "Ece")
    code = (await client.post("/v1/classrooms", json={"name": "8-C"}, headers=teacher)).json()[
        "join_code"
    ]
    response = await client.post(
        f"/v1/children/{child_id}/classrooms", json={"code": code}, headers=stranger
    )
    assert response.status_code == 404


async def test_heatmap_counts_and_privacy(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    teacher = await _login(client, "ogr-5@example.com", "teacher")
    guardian = await _login(client, "veli-c5@example.com", "guardian")
    ali = await _child(client, guardian, "Ali")
    zeynep = await _child(client, guardian, "Zeynep")
    unapproved = await _child(client, guardian, "Gizli")
    classroom = (await client.post("/v1/classrooms", json={"name": "6-A"}, headers=teacher)).json()
    for child_id in (ali, zeynep):
        await client.post(
            f"/v1/children/{child_id}/classrooms",
            json={"code": classroom["join_code"]},
            headers=guardian,
        )
    # Ebeveyn onayı olmayan kayıt öğretmene görünmemeli.
    db_session.add(
        Enrollment(
            classroom_id=uuid.UUID(classroom["id"]),
            child_id=uuid.UUID(unapproved),
            guardian_approved=False,
        )
    )
    await _study(db_session, ali, "Kesirler", problems=2, solved=2, hints=1)
    await _study(db_session, ali, "yüzdeler", problems=2, solved=0, hints=4)
    await _study(db_session, zeynep, "kesirler ", problems=2, solved=2, hints=0)
    await _study(db_session, unapproved, "kesirler", problems=5, solved=0, hints=5)
    await record_event(
        db_session,
        child_id=uuid.UUID(ali),
        problem_id=None,
        stage="input",
        source="problem",
        category="prompt_injection",
        severity=1,
        action="noticed",
    )
    await record_event(
        db_session,
        child_id=uuid.UUID(ali),
        problem_id=None,
        stage="input",
        source="problem",
        category="self_harm",
        severity=3,
        action="blocked",
    )
    await db_session.commit()

    response = await client.get(f"/v1/classrooms/{classroom['id']}/heatmap", headers=teacher)
    assert response.status_code == 200
    body = response.json()
    assert body["classroom"]["student_count"] == 2
    assert [s["nickname"] for s in body["students"]] == ["Ali", "Zeynep"]
    ali_row = body["students"][0]
    assert (ali_row["problems"], ali_row["solved"], ali_row["avg_hints"]) == (4, 2, 2.5)
    assert ali_row["answer_requests"] == 1
    # Konular küçük harfe birleştirilir; en zor konu en üstte.
    assert [(t["topic"], t["problems"], t["struggling"]) for t in body["topics"]] == [
        ("yüzdeler", 2, 1),
        ("kesirler", 4, 0),
    ]
    assert len(body["cells"]) == 3
    # Gizlilik: soru/ipucu metni ve güvenlik uyarısı öğretmene hiçbir biçimde gitmez.
    for secret in ("GİZLİ SORU METNİ", "GİZLİ İPUCU", "self_harm", "Gizli"):
        assert secret not in response.text


async def test_demo_teacher_shortcut_builds_classroom(db_session: AsyncSession) -> None:
    dev_app = FastAPI()
    dev_app.include_router(dev_router)

    async def override_get_db():  # type: ignore[no-untyped-def]
        yield db_session

    dev_app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=dev_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/v1/dev/demo-teacher")
        second = await client.post("/v1/dev/demo-teacher")
    assert first.status_code == 200 and second.status_code == 200
    rows = (await db_session.execute(Enrollment.__table__.select())).all()
    assert len(rows) == 5  # demo çocuk + 4 sentetik öğrenci; ikinci çağrı tekrar eklemez
