"""Zero-dependency in-memory sliding-window rate limiter ASGI middleware."""

import json
import time
from collections import defaultdict
from typing import Dict, List
from starlette.types import ASGIApp, Receive, Scope, Send
from backend.core.config import get_settings
from backend.core.logging import logger


class SlidingWindowRateLimiter:
    """Pure ASGI Sliding window rate limiter per client IP for /api/* endpoints.

    Avoids BaseHTTPMiddleware lock deadlocks with anyio on Windows / Python 3.15.
    """

    def __init__(self, app: ASGIApp, requests_per_minute: int = 30):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60.0
        self.client_records: Dict[str, List[float]] = defaultdict(list)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        settings = get_settings()
        path = scope.get("path", "")

        # Bypass rate limiter in test mode or non-API routes
        if settings.test_mode or not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        # Extract client IP from headers or client tuple
        headers = dict(scope.get("headers", []))
        forwarded_for = headers.get(b"x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.decode("latin1").split(",")[0].strip()
        else:
            client = scope.get("client")
            client_ip = client[0] if client else "127.0.0.1"

        current_time = time.time()
        window_start = current_time - self.window_seconds

        timestamps = self.client_records[client_ip]
        valid_timestamps = [t for t in timestamps if t > window_start]

        if len(valid_timestamps) >= self.requests_per_minute:
            logger.warning(
                f"[RateLimiter] Rate limit exceeded for IP: {client_ip} on {path}"
            )
            oldest_timestamp = valid_timestamps[0]
            retry_after = max(1, int(self.window_seconds - (current_time - oldest_timestamp)))
            body = json.dumps(
                {"detail": "Rate limit exceeded. Too many requests. Please retry later."}
            ).encode("utf-8")

            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", str(retry_after).encode("ascii")),
                    (b"x-ratelimit-limit", str(self.requests_per_minute).encode("ascii")),
                    (b"x-ratelimit-remaining", b"0"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": body,
            })
            return

        valid_timestamps.append(current_time)
        self.client_records[client_ip] = valid_timestamps
        remaining = max(0, self.requests_per_minute - len(valid_timestamps))

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers_list = list(message.get("headers", []))
                headers_list.append((b"x-ratelimit-limit", str(self.requests_per_minute).encode("ascii")))
                headers_list.append((b"x-ratelimit-remaining", str(remaining).encode("ascii")))
                message["headers"] = headers_list
            await send(message)

        await self.app(scope, receive, send_wrapper)
