"""Yerel deneme kısayolları: varsayılan kapalı, şemada görünmez, açıkken demo oturumu verir."""

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.db import get_db
from app.core.security import decode_token
from app.main import app
from app.modules.dev.router import dev_router


def test_dev_shortcuts_are_off_by_default() -> None:
    assert Settings(_env_file=None).dev_shortcuts is False


def test_dev_routes_are_not_in_openapi_schema() -> None:
    assert not any(path.startswith("/v1/dev") for path in app.openapi()["paths"])


async def test_demo_child_token_opens_child_session(db_session: AsyncSession) -> None:
    dev_app = FastAPI()
    dev_app.include_router(dev_router)

    async def override_get_db():  # type: ignore[no-untyped-def]
        yield db_session

    dev_app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=dev_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.post("/v1/dev/demo-child")
        second = await client.post("/v1/dev/demo-child")
        guardian = await client.post("/v1/dev/demo-guardian")

    assert first.status_code == 200 and second.status_code == 200
    a, b = (decode_token(r.json()["access_token"]) for r in (first, second))
    assert a["role"] == "child" and a["sub"] == b["sub"]  # aynı demo çocuk yeniden kullanılır
    assert guardian.status_code == 200 and guardian.json()["refresh_token"]
