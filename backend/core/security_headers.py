"""Pure ASGI Security Headers Middleware."""

from starlette.types import ASGIApp, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """Pure ASGI middleware injecting defensive security headers.

    Avoids BaseHTTPMiddleware lock deadlocks with anyio on Windows / Python 3.15.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"permissions-policy", b"camera=(self), microphone=()"),
                    (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
                ])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
