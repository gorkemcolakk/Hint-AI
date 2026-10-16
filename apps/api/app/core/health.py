import asyncio
from typing import Any

_PROBE_TIMEOUT = 2.0


async def check_database(url: str) -> dict[str, Any]:
    """Postgres'e SELECT 1 ile bağlanmayı dener; sonucu durum sözlüğü olarak döner."""

    def _probe() -> None:
        import psycopg

        with psycopg.connect(url, connect_timeout=2) as conn:
            conn.execute("SELECT 1")

    try:
        await asyncio.wait_for(asyncio.to_thread(_probe), timeout=_PROBE_TIMEOUT)
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


async def check_redis(url: str) -> dict[str, Any]:
    """Redis'e PING atar; sonucu durum sözlüğü olarak döner."""

    async def _probe() -> None:
        import redis.asyncio as aioredis

        client = aioredis.from_url(url, socket_connect_timeout=2)
        try:
            await client.ping()
        finally:
            await client.aclose()

    try:
        await asyncio.wait_for(_probe(), timeout=_PROBE_TIMEOUT)
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
