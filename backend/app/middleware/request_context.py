"""
Request context middleware for Quantum Market Intelligence.
"""

from __future__ import annotations

import time
import uuid
import logging
logger = logging.getLogger("qmi.api")

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Attach request metadata to every HTTP request.

    The middleware generates a unique request ID and measures the total
    request execution time.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        started_at = time.perf_counter()

        request.state.request_id = request_id

        response = await call_next(request)

        execution_time_ms = round(
            (time.perf_counter() - started_at) * 1000,
            3,
        )

        request.state.execution_time_ms = execution_time_ms

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Execution-Time-Ms"] = str(execution_time_ms)

        logger.info(
    "%s %s | status=%s | request_id=%s | %.3f ms",
    request.method,
    request.url.path,
    response.status_code,
    request_id,
    execution_time_ms,
)
        return response