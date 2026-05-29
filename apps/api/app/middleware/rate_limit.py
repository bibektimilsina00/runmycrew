"""Rate limiting via slowapi (wraps limits library, backed by Redis)."""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def _get_key(request: Request) -> str:
    """Use authenticated user ID when available, fall back to IP."""
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return str(user.id)
    return get_remote_address(request)


limiter = Limiter(key_func=_get_key)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please slow down.",
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )
