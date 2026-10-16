from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_returns_ok() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz_returns_structured_status() -> None:
    response = client.get("/readyz")
    assert response.status_code in (200, 503)
    body = response.json()
    assert body["status"] in ("ready", "not_ready")
    assert "database" in body["checks"]
    assert "redis" in body["checks"]
