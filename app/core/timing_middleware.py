"""Middleware: замер времени обработки HTTP-запросов.

Добавляет заголовок ``X-Process-Time`` (секунды) и пишет в лог медленные запросы.
Полезно для локального профилирования и для ``scripts/benchmark_api.py``.
"""
from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.timing")

# Порог для предупреждения в логах (мс). Ниже — только DEBUG.
SLOW_REQUEST_MS = 200.0


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        response.headers["X-Process-Time"] = f"{elapsed_ms / 1000.0:.6f}"
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"

        path = request.url.path
        method = request.method
        status = response.status_code
        if elapsed_ms >= SLOW_REQUEST_MS:
            logger.warning(
                "slow request %.1fms %s %s → %s",
                elapsed_ms,
                method,
                path,
                status,
            )
        else:
            logger.debug(
                "%.1fms %s %s → %s",
                elapsed_ms,
                method,
                path,
                status,
            )
        return response
