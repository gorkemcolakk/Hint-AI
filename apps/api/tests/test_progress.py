"""Ebeveyn özeti (A4): sayımların doğruluğu, gizlilik ve güvenlik uyarısı politikası."""

import uuid
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.problems.models import HiddenSolution, Problem
from app.modules.safety.models import record_event
from app.modules.tutoring.models import Attempt, Hint

PASSWORD = "gizli-parola-123"


async def _guardian_with_child(
    client: httpx.AsyncClient, email: str, birth_year: int = 2014
) -> tuple[dict[str, str], uuid.UUID]:
    await client.post(
        "/v1/auth/register", json={"email": email, "password": PASSWORD, "role": "guardian"}
    )
    login = await client.post("/v1/auth/login", json={"email": email, "password": PASSWORD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    child = await client.post(
        "/v1/children",
        json={"nickname": "Deniz", "birth_year": birth_year, "grade": 7, "purposes": ["service"]},
        headers=headers,
    )
    return headers, uuid.UUID(child.json()["id"])


def _solution(topic: str) -> HiddenSolution:
    return HiddenSolution(
        problem_hash=uuid.uuid4().hex,
        topic=topic,
        steps=["adım"],
        final_answer="5",
        verified=True,
        prompt_version="test",
        model="test",
    )


async def _problem(
    db: AsyncSession,
    child_id: uuid.UUID,
    *,
    topic: str,
    solved: bool,
    hints: int,
    attempts: int,
    created_at: datetime | None = None,
) -> Problem:
    solution = _solution(topic)
    db.add(solution)
    await db.flush()
    problem = Problem(
        child_id=child_id,
        masked_text=f"[ISIM] soru ({topic})",
        problem_hash=solution.problem_hash,
        status="verified",
        solution_id=solution.id,
        state="solved" if solved else "open",
    )
    if created_at is not None:
        problem.created_at = created_at
    db.add(problem)
    await db.flush()
    for level in range(hints):
        db.add(
            Hint(
                problem_id=problem.id,
                level=level,
                content="ipucu",
                source="fallback",
                leak_check={},
            )
        )
    for _ in range(attempts):
        db.add(Attempt(problem_id=problem.id, answer_masked="6", is_correct=False))
    await db.commit()
    return problem


async def test_summary_counts_are_correct(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    headers, child_id = await _guardian_with_child(client, "rapor-1@example.com")
    await _problem(db_session, child_id, topic="kesirler", solved=True, hints=0, attempts=1)
    await _problem(db_session, child_id, topic="kesirler", solved=True, hints=3, attempts=2)
    await _problem(db_session, child_id, topic="denklem", solved=False, hints=2, attempts=3)
    # Dönem dışı (10 gün önce) soru sayılmaz.
    await _problem(
        db_session,
        child_id,
        topic="eski",
        solved=True,
        hints=0,
        attempts=0,
        created_at=datetime.now(UTC) - timedelta(days=10),
    )

    response = await client.get(f"/v1/children/{child_id}/summary?days=7", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["problems_started"] == 3
    assert body["problems_solved"] == 2
    assert body["solved_without_hints"] == 1
    assert body["avg_hints_per_solved"] == 1.5
    assert body["hints_total"] == 5 and body["attempts_total"] == 6
    assert body["topics"] == [
        {"topic": "kesirler", "problems": 2, "solved": 2},
        {"topic": "denklem", "problems": 1, "solved": 0},
    ]
    # Varsayılan gizlilik: özet; soru metni gösterilmez.
    assert body["shows_problem_text"] is False
    assert all(item["text"] is None for item in body["recent"])

    wide = await client.get(f"/v1/children/{child_id}/summary?days=30", headers=headers)
    assert wide.json()["problems_started"] == 4


async def test_empty_period(client: httpx.AsyncClient, db_session: AsyncSession) -> None:
    headers, child_id = await _guardian_with_child(client, "rapor-2@example.com")
    body = (await client.get(f"/v1/children/{child_id}/summary", headers=headers)).json()
    assert body["problems_started"] == 0 and body["avg_hints_per_solved"] is None
    assert body["topics"] == [] and body["recent"] == [] and body["alerts"] == []


async def test_full_transcript_setting_shows_masked_text(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    headers, child_id = await _guardian_with_child(client, "rapor-3@example.com")
    await client.patch(
        f"/v1/children/{child_id}", json={"privacy_level": "full_transcript"}, headers=headers
    )
    await _problem(db_session, child_id, topic="kesirler", solved=False, hints=0, attempts=0)
    body = (await client.get(f"/v1/children/{child_id}/summary", headers=headers)).json()
    assert body["shows_problem_text"] is True
    assert body["recent"][0]["text"] == "[ISIM] soru (kesirler)"  # yalnızca maskeli hali


async def test_safety_alerts_follow_guardian_policy(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    headers, child_id = await _guardian_with_child(client, "rapor-4@example.com")
    for category, severity in (
        ("self_harm", 3),
        ("abuse_disclosure", 3),
        ("bullying", 1),
        ("prompt_injection", 1),
        ("prompt_injection", 1),
    ):
        await record_event(
            db_session,
            child_id=child_id,
            problem_id=None,
            stage="input",
            source="problem",
            category=category,
            severity=severity,
            action="blocked",
        )
    await db_session.commit()

    response = await client.get(f"/v1/children/{child_id}/summary", headers=headers)
    body = response.json()
    assert [a["title"] for a in body["alerts"]] == ["Kendine zarar verme ile ilgili bir ifade"]
    # İstismar bildirimi ebeveyne hiçbir biçimde görünmez (zarar veren ebeveyn olabilir).
    assert "istismar" not in response.text.lower() and "abuse" not in response.text
    assert body["flags"] == {"Zorbalık anlatımı": 1}
    assert body["answer_requests"] == 2


async def test_other_guardians_child_is_not_found(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    _, child_id = await _guardian_with_child(client, "rapor-5@example.com")
    other, _ = await _guardian_with_child(client, "rapor-6@example.com")
    response = await client.get(f"/v1/children/{child_id}/summary", headers=other)
    assert response.status_code == 404
