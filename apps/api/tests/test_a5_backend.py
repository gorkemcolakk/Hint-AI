"""A5 backend tamamlayıcı entegrasyon testleri:
- Auth brute-force rate limit (M1-1)
- İpucu geri bildirimi (POST /v1/hints/{id}/feedback + IDOR kontrolü)
- Sızıntı doğrulamalı SSE ipucu akışı (POST /v1/problems/{id}/hints + Accept: text/event-stream)
- Günlük yeni soru sınırı (Bölüm 5.5: yeni soru 429, açık soru devam eder)
- KVKK veri dışa aktarma ve silme (GET /export + DELETE /children/{id} CASCADE + gizlilik)
- Yapılandırılmış gözlemlenebilirlik (X-Request-ID + PII sızdırmayan JSON log)
"""

import json
import logging
import uuid

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limiter
from app.main import app
from app.modules.llm_gateway.models import LLMCall
from app.modules.llm_gateway.providers import BaseLLMProvider, LLMMessage, LLMResponse
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.problems.models import Problem
from app.modules.problems.router import get_llm_gateway
from app.modules.safety.models import record_event
from app.modules.tutoring.models import Hint

SOLVE_JSON = json.dumps(
    {
        "grade": 7,
        "topic": "birinci dereceden denklem",
        "steps": ["Her iki taraftan 5 çıkar: 3x = 15", "Her iki tarafı 3'e böl"],
        "final_answer": "5",
        "sympy_check": {"type": "solve", "equation": "3*x + 5 = 20", "variable": "x"},
    }
)
JUDGE_OK = json.dumps({"leak": False, "reason": "temiz", "severity": 0})
SAFE_HINT = "Önce eşitliğin iki tarafından da 5 çıkarırsak sağ tarafta kaç kalır?"


class StubTutorProvider(BaseLLMProvider):
    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        self._validate_messages(messages)
        sys_text = str(messages[0].content)
        if "ipucu yazarı" in sys_text:
            content = SAFE_HINT
        elif "kalite denetçisi" in sys_text:
            content = JUDGE_OK
        else:
            content = SOLVE_JSON
        return LLMResponse(content=content, input_tokens=20, output_tokens=15, latency_ms=5)


async def _setup_family(
    client: httpx.AsyncClient, email: str
) -> tuple[dict[str, str], str, dict[str, str]]:
    password = "gizli-parola-123"
    await client.post(
        "/v1/auth/register", json={"email": email, "password": password, "role": "guardian"}
    )
    login = await client.post("/v1/auth/login", json={"email": email, "password": password})
    guardian_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    child = await client.post(
        "/v1/children",
        json={
            "nickname": "Deniz",
            "birth_year": 2014,
            "grade": 7,
            "purposes": ["service", "llm_processing"],
        },
        headers=guardian_headers,
    )
    child_id = child.json()["id"]
    pairing = await client.post(f"/v1/children/{child_id}/device-pairing", headers=guardian_headers)
    paired = await client.post(
        "/v1/auth/child-pair", json={"child_id": child_id, "code": pairing.json()["code"]}
    )
    child_headers = {"Authorization": f"Bearer {paired.json()['access_token']}"}
    return guardian_headers, child_id, child_headers


async def test_auth_rate_limit_blocks_brute_force(client: httpx.AsyncClient) -> None:
    rate_limiter.reset()
    for _ in range(10):
        resp = await client.post(
            "/v1/auth/login", json={"email": "saldiri@example.com", "password": "yanlis-parola"}
        )
        assert resp.status_code == 401

    blocked = await client.post(
        "/v1/auth/login", json={"email": "saldiri@example.com", "password": "yanlis-parola"}
    )
    assert blocked.status_code == 429
    assert blocked.headers.get("retry-after") == "60"

    rate_limiter.reset()
    for i in range(10):
        reg = await client.post(
            "/v1/auth/register",
            json={"email": f"u{i}@example.com", "password": "gizli-parola-123", "role": "guardian"},
        )
        assert reg.status_code == 201
    reg_blocked = await client.post(
        "/v1/auth/register",
        json={"email": "u11@example.com", "password": "gizli-parola-123", "role": "guardian"},
    )
    assert reg_blocked.status_code == 429


async def test_hint_feedback_persists_and_blocks_other_child(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    app.dependency_overrides[get_llm_gateway] = lambda: LLMGatewayService(StubTutorProvider())
    _, _, child1 = await _setup_family(client, "fb-1@example.com")
    _, _, child2 = await _setup_family(client, "fb-2@example.com")

    created = await client.post(
        "/v1/problems", json={"text": "3x + 5 = 20 ise x kaçtır?"}, headers=child1
    )
    problem_id = created.json()["id"]
    hint_resp = await client.post(f"/v1/problems/{problem_id}/hints", json={}, headers=child1)
    hint_id = hint_resp.json()["hint"]["id"]

    ok = await client.post(f"/v1/hints/{hint_id}/feedback", json={"helpful": True}, headers=child1)
    assert ok.status_code == 200
    assert ok.json() == {"id": hint_id, "helpful": True}

    other = await client.post(
        f"/v1/hints/{hint_id}/feedback", json={"helpful": False}, headers=child2
    )
    assert other.status_code == 404

    row = await db_session.get(Hint, hint_id)
    assert row is not None and row.helpful is True


async def test_sse_hint_stream_delivers_verified_chunks_and_handles_crisis(
    client: httpx.AsyncClient,
) -> None:
    app.dependency_overrides[get_llm_gateway] = lambda: LLMGatewayService(StubTutorProvider())
    _, _, child = await _setup_family(client, "sse-1@example.com")

    created = await client.post(
        "/v1/problems", json={"text": "3x + 5 = 20 ise x kaçtır?"}, headers=child
    )
    problem_id = created.json()["id"]
    sse_headers = {**child, "Accept": "text/event-stream, application/json"}

    resp = await client.post(f"/v1/problems/{problem_id}/hints", json={}, headers=sse_headers)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "event: delta" in resp.text
    assert "event: hint" in resp.text
    assert "final_answer" not in resp.text

    deltas: list[str] = []
    final_event: dict[str, object] | None = None
    for block in resp.text.strip().split("\n\n"):
        lines = block.splitlines()
        event_type = lines[0].removeprefix("event:").strip()
        payload = json.loads(lines[1].removeprefix("data:").strip())
        if event_type == "delta":
            deltas.append(payload["text"])
        elif event_type == "hint":
            final_event = payload

    assert "".join(deltas) == SAFE_HINT
    assert final_event is not None
    assert final_event["level"] == 0
    assert final_event["text"] == SAFE_HINT

    # Kriz mesajı SSE modunda da LLM'e gitmeden sabit destek kartı döner.
    crisis = await client.post(
        f"/v1/problems/{problem_id}/hints",
        json={"message": "artık yaşamak istemiyorum"},
        headers=sse_headers,
    )
    assert crisis.status_code == 200
    assert '"hint": null' in crisis.text
    assert "112" in crisis.text


async def test_daily_new_problem_limit_allows_finishing_open_problem(
    client: httpx.AsyncClient,
) -> None:
    app.dependency_overrides[get_llm_gateway] = lambda: LLMGatewayService(StubTutorProvider())
    guardian, child_id, child = await _setup_family(client, "limit-1@example.com")

    patched = await client.patch(
        f"/v1/children/{child_id}", json={"daily_new_problem_limit": 1}, headers=guardian
    )
    assert patched.status_code == 200

    first = await client.post(
        "/v1/problems", json={"text": "3x + 5 = 20 ise x kaçtır?"}, headers=child
    )
    assert first.status_code == 201
    problem_id = first.json()["id"]

    second = await client.post(
        "/v1/problems", json={"text": "2x + 4 = 10 ise x kaçtır?"}, headers=child
    )
    assert second.status_code == 429

    # Başlanmış soru sınır dolsa da tamamlanabilir (Bölüm 5.5).
    hint = await client.post(f"/v1/problems/{problem_id}/hints", json={}, headers=child)
    assert hint.status_code == 200
    solved = await client.post(
        f"/v1/problems/{problem_id}/attempts", json={"answer": "5"}, headers=child
    )
    assert solved.status_code == 200 and solved.json()["solved"] is True


async def test_kvkk_export_and_delete_child_cascade(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    app.dependency_overrides[get_llm_gateway] = lambda: LLMGatewayService(StubTutorProvider())
    guardian, child_id, child = await _setup_family(client, "kvkk-1@example.com")
    other_guardian, _, _ = await _setup_family(client, "kvkk-2@example.com")

    created = await client.post(
        "/v1/problems",
        json={"text": "Benim adım Deniz, 3x + 5 = 20 ise x kaçtır?"},
        headers=child,
    )
    problem_id = created.json()["id"]
    await client.post(f"/v1/problems/{problem_id}/hints", json={}, headers=child)
    await record_event(
        db_session,
        child_id=uuid.UUID(child_id),
        problem_id=None,
        stage="input",
        source="problem",
        category="abuse_disclosure",
        severity=3,
        action="blocked",
    )
    await db_session.commit()

    # Başka ebeveyn erişemez
    other_exp = await client.get(f"/v1/children/{child_id}/export", headers=other_guardian)
    other_del = await client.delete(f"/v1/children/{child_id}", headers=other_guardian)
    assert other_exp.status_code == 404 and other_del.status_code == 404

    # Varsayılan summary_only: soru metni boş, gizli cevap ve istismar kaydı yok
    exp_summary = await client.get(f"/v1/children/{child_id}/export", headers=guardian)
    assert exp_summary.status_code == 200
    body = exp_summary.json()
    assert body["shows_problem_text"] is False
    assert body["problems"][0]["text"] is None
    assert "final_answer" not in exp_summary.text
    assert "abuse_disclosure" not in exp_summary.text

    # full_transcript açılınca yalnızca maskeli metin gelir
    await client.patch(
        f"/v1/children/{child_id}", json={"privacy_level": "full_transcript"}, headers=guardian
    )
    exp_full = await client.get(f"/v1/children/{child_id}/export", headers=guardian)
    assert exp_full.json()["problems"][0]["text"].startswith("Benim adım [ISIM]")

    # Silme: çocuk ve soruları silinir; llm_calls anonimleşerek (child_id=None) kalır
    deleted = await client.delete(f"/v1/children/{child_id}", headers=guardian)
    assert deleted.status_code == 204
    assert (await client.get(f"/v1/children/{child_id}", headers=guardian)).status_code == 404
    assert await db_session.get(Problem, problem_id) is None

    calls = (await db_session.scalars(select(LLMCall))).all()
    assert len(calls) >= 1
    assert all(str(call.child_id) != child_id for call in calls)


async def test_structured_logging_sets_request_id_and_omits_pii(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    app.dependency_overrides[get_llm_gateway] = lambda: LLMGatewayService(StubTutorProvider())
    _, _, child = await _setup_family(client, "obs-1@example.com")

    with caplog.at_level(logging.INFO, logger="hint.http"):
        resp = await client.post(
            "/v1/problems?gizli_kod=998877",
            json={"text": "Benim adım Zeynep, 3x + 5 = 20 ise x kaçtır?"},
            headers={**child, "X-Request-ID": "req-test-42"},
        )

    assert resp.status_code == 201
    assert resp.headers["x-request-id"] == "req-test-42"

    logged = "\n".join(record.message for record in caplog.records if record.name == "hint.http")
    assert '"request_id": "req-test-42"' in logged
    assert '"path": "/v1/problems"' in logged
    assert "Zeynep" not in logged
    assert "3x + 5" not in logged
    assert "998877" not in logged
