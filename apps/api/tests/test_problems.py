"""POST /v1/problems uçtan uca testleri (gerçek DB, sahte LLM sağlayıcısı)."""

import json

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.llm_gateway.providers import MockLLMProvider
from app.modules.llm_gateway.service import LLMGatewayService
from app.modules.problems.models import HiddenSolution, Problem
from app.modules.problems.router import get_llm_gateway

CORRECT = json.dumps(
    {
        "grade": 7,
        "topic": "birinci dereceden denklem",
        "steps": ["Her iki taraftan 5 çıkar", "3'e böl"],
        "final_answer": "5",
        "sympy_check": {"type": "solve", "equation": "3*x + 5 = 20", "variable": "x"},
    }
)
WRONG = CORRECT.replace('"final_answer": "5"', '"final_answer": "6"')


def _use_provider(provider: MockLLMProvider) -> None:
    app.dependency_overrides[get_llm_gateway] = lambda: LLMGatewayService(provider=provider)


async def _child_headers(
    client: httpx.AsyncClient, email: str, purposes: list[str]
) -> dict[str, str]:
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "gizli-parola-123", "role": "guardian"},
    )
    login = await client.post(
        "/v1/auth/login", json={"email": email, "password": "gizli-parola-123"}
    )
    guardian = {"Authorization": f"Bearer {login.json()['access_token']}"}
    child = await client.post(
        "/v1/children",
        json={"nickname": "Deniz", "birth_year": 2014, "grade": 7, "purposes": purposes},
        headers=guardian,
    )
    child_id = child.json()["id"]
    pairing = await client.post(f"/v1/children/{child_id}/device-pairing", headers=guardian)
    paired = await client.post(
        "/v1/auth/child-pair", json={"child_id": child_id, "code": pairing.json()["code"]}
    )
    return {"Authorization": f"Bearer {paired.json()['access_token']}"}


async def test_problem_is_solved_verified_and_answer_never_returned(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    provider = MockLLMProvider(canned_response=CORRECT)
    _use_provider(provider)
    headers = await _child_headers(client, "veli-p1@example.com", ["service", "llm_processing"])

    resp = await client.post(
        "/v1/problems",
        json={"text": "Benim adım Deniz. 3x + 5 = 20 ise x kaçtır?"},
        headers=headers,
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "verified"
    assert body["topic"] == "birinci dereceden denklem"
    # Gizli çözüm öğrenciye dönmez: ne adımlar ne nihai cevap yanıtta yer alır.
    assert set(body) == {"id", "status", "grade", "topic", "notice", "safety"}
    # Soru metninde isim var: maskelenir ve çocuğa nazik bir not gösterilir.
    assert body["safety"] is None and "gerek yok" in body["notice"]
    assert "çıkar" not in resp.text

    problem = await db_session.scalar(select(Problem))
    assert problem is not None
    assert "Deniz" not in problem.masked_text and "[ISIM]" in problem.masked_text
    solution = await db_session.get(HiddenSolution, problem.solution_id)
    assert solution is not None and solution.verified and solution.final_answer == "5"
    assert provider.call_count == 1


async def test_mismatch_is_retried_then_marked_low_confidence(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    provider = MockLLMProvider(canned_response=WRONG)
    _use_provider(provider)
    headers = await _child_headers(client, "veli-p2@example.com", ["service", "llm_processing"])

    resp = await client.post("/v1/problems", json={"text": "3x + 5 = 20, x?"}, headers=headers)

    assert resp.status_code == 201
    assert resp.json()["status"] == "low_confidence"
    assert provider.call_count == 2
    solution = await db_session.scalar(select(HiddenSolution))
    assert solution is not None and solution.verified is False


async def test_verified_solution_is_reused_for_same_problem(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    provider = MockLLMProvider(canned_response=CORRECT)
    _use_provider(provider)
    headers = await _child_headers(client, "veli-p3@example.com", ["service", "llm_processing"])

    for text in ("3x + 5 = 20 ise x kaçtır?", "  3X + 5 = 20 ise   x kaçtır? "):
        resp = await client.post("/v1/problems", json={"text": text}, headers=headers)
        assert resp.json()["status"] == "verified"

    assert provider.call_count == 1
    assert await db_session.scalar(select(func.count(HiddenSolution.id))) == 1
    assert await db_session.scalar(select(func.count(Problem.id))) == 2


async def test_unparseable_model_output_marks_problem_failed(
    client: httpx.AsyncClient,
) -> None:
    provider = MockLLMProvider(canned_response="Üzgünüm, JSON veremem.")
    _use_provider(provider)
    headers = await _child_headers(client, "veli-p4@example.com", ["service", "llm_processing"])

    resp = await client.post("/v1/problems", json={"text": "2 + 2 kaç?"}, headers=headers)

    assert resp.status_code == 201
    assert resp.json()["status"] == "failed"
    assert provider.call_count == 2


async def test_problem_requires_llm_processing_consent(client: httpx.AsyncClient) -> None:
    provider = MockLLMProvider(canned_response=CORRECT)
    _use_provider(provider)
    headers = await _child_headers(client, "veli-p5@example.com", ["service"])

    resp = await client.post("/v1/problems", json={"text": "3x + 5 = 20"}, headers=headers)

    assert resp.status_code == 403
    assert provider.call_count == 0


async def test_problem_requires_child_token(client: httpx.AsyncClient) -> None:
    resp = await client.post("/v1/problems", json={"text": "3x + 5 = 20"})
    assert resp.status_code == 401
