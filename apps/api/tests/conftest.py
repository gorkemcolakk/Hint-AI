import os
from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.modules.llm_gateway.models  # noqa: F401
import app.modules.problems.models  # noqa: F401
from app.modules.auth_consent.models import Base

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

_TABLES = (
    "problems",
    "hidden_solutions",
    "llm_calls",
    "pairing_codes",
    "consents",
    "refresh_tokens",
    "child_profiles",
    "users",
)

_database_ready = False


async def _ensure_test_database(url: str) -> None:
    """Test veritabanı yoksa oluşturur. Testler tabloları boşalttığı için adı _test ile bitmeli."""
    global _database_ready
    if _database_ready:
        return
    target = make_url(url)
    name = target.database or ""
    if not name.endswith("_test"):
        pytest.fail(
            f"TEST_DATABASE_URL '{name}' veritabanını gösteriyor; testler tabloları boşalttığı "
            "için adı _test ile biten ayrı bir veritabanı kullanın (ör. hint_test)."
        )
    admin = create_async_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{name}"'))
    await admin.dispose()
    _database_ready = True


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL tanımlı değil; DB entegrasyon testi atlandı")
    await _ensure_test_database(TEST_DATABASE_URL)
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        for table in _TABLES:
            await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        await session.commit()
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    from app.core.db import get_db
    from app.main import app

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
