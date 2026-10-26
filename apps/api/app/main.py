from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.health import check_database, check_redis
from app.modules.auth_consent.router import auth_router, children_router

app = FastAPI(title=settings.service_name, version="0.1.0")

# Kimlik Bearer header ile taşınır, cookie yok; bu yüzden credentials kapalı.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(children_router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/readyz")
async def readyz(response: Response) -> dict[str, object]:
    database = await check_database(settings.database_url)
    redis = await check_redis(settings.redis_url)
    ready = bool(database.get("ok")) and bool(redis.get("ok"))
    if not ready:
        response.status_code = 503
    return {
        "status": "ready" if ready else "not_ready",
        "checks": {"database": database, "redis": redis},
    }
