"""Kayan pencereli hız sınırlayıcı (M1-1 / Bölüm 9.3 & 10.3).

Kimlik doğrulama ve cihaz eşleştirme uçlarında kaba kuvvet (brute-force) denemelerini sınırlar.
Redis yapılandırılmış ve erişilebilirse Redis sayaçlarını, aksi halde süreç içi bellek
pencerelerini kullanır (yerel geliştirme ve testlerde Redis zorunluluğu yaratmaz).
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import settings

RATE_LIMIT_MESSAGE = "Çok fazla deneme yapıldı. Lütfen biraz bekleyip tekrar dene."


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def reset(self) -> None:
        self._buckets.clear()

    def allow_memory(self, key: str, *, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        bucket = self._buckets[key]
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    async def check(self, key: str, *, limit: int, window_seconds: int = 60) -> None:
        allowed = await self._allow_redis_or_memory(key, limit=limit, window_seconds=window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=RATE_LIMIT_MESSAGE,
                headers={"Retry-After": str(window_seconds)},
            )

    async def _allow_redis_or_memory(self, key: str, *, limit: int, window_seconds: int) -> bool:
        if settings.redis_url:
            try:
                from redis.asyncio import Redis

                client = Redis.from_url(settings.redis_url, socket_connect_timeout=0.3)
                try:
                    redis_key = f"hint:rl:{key}"
                    current = int(await client.incr(redis_key))
                    if current == 1:
                        await client.expire(redis_key, window_seconds)
                    return current <= limit
                finally:
                    await client.aclose()
            except Exception:
                # Redis kapalıysa bellek içi sınırlayıcıya zarifçe düş.
                pass
        return self.allow_memory(key, limit=limit, window_seconds=window_seconds)


rate_limiter = SlidingWindowLimiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"
