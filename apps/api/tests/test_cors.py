from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def _preflight(origin: str) -> dict[str, str]:
    response = client.options(
        "/v1/children",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    return dict(response.headers)


def test_cors_allows_configured_origin() -> None:
    origin = settings.cors_origins[0]
    headers = _preflight(origin)
    assert headers["access-control-allow-origin"] == origin
    assert "access-control-allow-credentials" not in headers


def test_cors_rejects_unknown_origin() -> None:
    headers = _preflight("https://kotu-niyetli.example")
    assert "access-control-allow-origin" not in headers
