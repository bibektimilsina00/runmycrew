"""Error tracking / tracing via Sentry.

A no-op unless `SENTRY_DSN` is configured, so it's safe to call unconditionally
at startup in both the API and the worker. When a DSN is set, sentry-sdk's
auto-integrations cover FastAPI, Celery, SQLAlchemy, and Redis.
"""

from apps.api.app.core.config import settings
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

_initialized = False


def init_sentry() -> None:
    global _initialized
    if _initialized or not settings.SENTRY_DSN:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            # Tag every event with the deployed image sha so errors map to
            # a release. Empty → sentry-sdk falls back to auto-detection.
            release=settings.RELEASE or None,
            send_default_pii=False,
        )
        _initialized = True
        logger.info("Sentry initialized (environment=%s)", settings.ENVIRONMENT)
    except Exception as exc:  # never let observability setup break startup
        logger.warning("Sentry initialization skipped: %s", exc)
