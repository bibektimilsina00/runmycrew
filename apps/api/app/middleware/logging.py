import logging
import time

logger = logging.getLogger("fuse")


class LoggingMiddleware:
    """Pure-ASGI logging middleware.

    Implemented as a raw ASGI callable instead of `BaseHTTPMiddleware`
    because Starlette's `BaseHTTPMiddleware` swallows WebSocket upgrade
    requests — it wraps the scope as HTTP-only and the upgrade handshake
    never reaches the route handler. Passing non-HTTP scopes through
    untouched keeps WS endpoints (`/ws/executions/...` etc.) working.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        status_holder: dict[str, int] = {"status": 0}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
            await send(message)

        await self.app(scope, receive, send_wrapper)
        duration = time.time() - start_time
        path = scope.get("path", "")
        method = scope.get("method", "")
        logger.info(
            f"Method: {method} Path: {path} Status: {status_holder['status']} Duration: {duration:.4f}s"
        )
