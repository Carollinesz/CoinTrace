import math
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

WINDOW_SECONDS = 60
EXEMPT_PATHS = {"/health"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed one-minute window per client IP, kept in memory (single instance only).

    All counters reset together when the window rolls over, so memory stays bounded
    by the number of distinct IPs seen in one minute.
    """

    def __init__(self, app, limit_per_minute: int):
        super().__init__(app)
        self.limit_per_minute = limit_per_minute
        self.window_start = time.monotonic()
        self.hits_by_client: dict[str, int] = {}

    async def dispatch(self, request: Request, call_next):
        if self.limit_per_minute <= 0 or request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        now = time.monotonic()
        if now - self.window_start >= WINDOW_SECONDS:
            self.window_start = now
            self.hits_by_client = {}

        client_ip = request.client.host if request.client else "unknown"
        hits = self.hits_by_client.get(client_ip, 0) + 1
        self.hits_by_client[client_ip] = hits

        if hits <= self.limit_per_minute:
            return await call_next(request)

        retry_after = math.ceil(WINDOW_SECONDS - (now - self.window_start))
        return JSONResponse(
            status_code=429,
            content={"message": "Too many requests, try again later"},
            headers={"Retry-After": str(max(retry_after, 1))},
        )
