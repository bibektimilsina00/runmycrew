from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from apps.api.app.api.router import router as api_router
from apps.api.app.core.config import settings
from apps.api.app.core.logger import get_logger
from apps.api.app.middleware.logging import LoggingMiddleware
from apps.api.app.middleware.rate_limit import limiter, rate_limit_exceeded_handler

logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Attach limiter to app state (required by slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Middleware (added in reverse execution order — first added = last to run on request)
app.add_middleware(LoggingMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.resolved_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check (exempt from rate limiting, no auth required) ────────────────


@app.get("/health", tags=["health"])
async def health_check():
    """Check API, DB, Redis and Celery worker connectivity."""
    import asyncio

    from apps.api.app.core.celery import celery_app

    status: dict = {"api": "ok", "db": "unknown", "redis": "unknown", "worker": "unknown"}
    http_status = 200

    # DB check
    try:
        import sqlalchemy as sa

        from apps.api.app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            await db.execute(sa.text("SELECT 1"))
        status["db"] = "ok"
    except Exception as e:
        status["db"] = f"error: {e}"
        http_status = 503

    # Redis check
    try:
        from apps.api.app.core.redis import get_redis

        redis = await get_redis()
        await redis.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {e}"
        http_status = 503

    # Celery worker check (non-blocking, 2s timeout)
    try:
        loop = asyncio.get_event_loop()

        def _ping():
            inspector = celery_app.control.inspect(timeout=2)
            return inspector.ping() or {}

        result = await loop.run_in_executor(None, _ping)
        status["worker"] = "ok" if result else "unreachable"
        if not result:
            http_status = max(http_status, 503)
    except Exception as e:
        status["worker"] = f"error: {e}"
        http_status = max(http_status, 503)

    overall = "ok" if http_status == 200 else "degraded"
    from fastapi.responses import JSONResponse

    return JSONResponse({"status": overall, **status}, status_code=http_status)


@app.get("/")
async def root():
    return {"message": "Welcome to Fuse API", "version": "1.0.0"}


app.include_router(api_router)
