from celery import Celery
from celery.schedules import crontab

# Eagerly register every SQLModel mapper in the worker / beat process.
# Without this, the first task that touches a model with a string-named
# `relationship('User')` (e.g. the polling scheduler hitting Workflow)
# triggers mapper init before `User` has been imported, and SQLAlchemy
# fails with "expression 'User' failed to locate a name". The API
# process gets this for free during FastAPI startup; worker / beat
# don't, so we do it here at the celery_app import boundary.
import apps.api.app.shared.model  # noqa: F401, E402
from apps.api.app.core.config import settings
from apps.api.app.core.observability import init_sentry

# Initialize Sentry for the worker process (no-op unless SENTRY_DSN is set).
init_sentry()

celery_app = Celery(
    "fuse",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "apps.worker.app.jobs.tasks",
        "apps.api.app.execution_engine.scheduler.cron",
        "apps.api.app.execution_engine.scheduler.integration_polling",
        "apps.api.app.features.triggers.polling_listener",
        "apps.api.app.features.triggers.listen_sweeper",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "check-cron-triggers": {
            "task": "check_cron_triggers",
            "schedule": crontab(minute="*"),
        },
        "poll-integration-triggers": {
            "task": "poll_integration_triggers",
            "schedule": 30.0,
        },
        "sweep-polling-listens": {
            "task": "sweep_polling_listens",
            "schedule": 60.0,
        },
    },
)
