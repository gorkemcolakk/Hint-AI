"""Gizlilik odaklı yapılandırılmış gözlemlenebilirlik ara katmanı (Bölüm 13.3).

Kurallar (AGENTS.md Kural 3):
- İstek/yanıt gövdesi (soru metni, cevap, parola), sorgu dizgisi (eşleştirme kodu vb.) ve
  yetkilendirme başlıkları ASLA loglanmaz.
- Yalnızca `request_id`, HTTP metodu, temiz yol (`path`), durum kodu ve gecikme (`latency_ms`)
  yapılandırılmış JSON olarak kaydedilir ve yanıta `X-Request-ID` başlığı eklenir.
"""

import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

request_logger = logging.getLogger("hint.http")


def format_http_event(
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    latency_ms: int,
) -> str:
    return json.dumps(
        {
            "event": "http_request",
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "latency_ms": latency_ms,
        },
        ensure_ascii=False,
    )


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get("x-request-id", "").strip()
        request_id = incoming[:64] if incoming and incoming.isascii() else str(uuid.uuid4())
        start = time.monotonic()
        response = await call_next(request)
        latency_ms = int((time.monotonic() - start) * 1000)

        response.headers["X-Request-ID"] = request_id
        request_logger.info(
            format_http_event(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                latency_ms=latency_ms,
            )
        )
        return response
