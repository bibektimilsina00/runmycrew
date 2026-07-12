import pytest

from apps.api.app.core.config import settings
from apps.api.app.middleware.rate_limit import limiter


@pytest.fixture(autouse=True)
def _force_process_sandbox(monkeypatch):
    """Keep the suite deterministic and fast: Code-node tests use the in-process
    executor regardless of whether a Docker runtime is present. The container
    executor is exercised explicitly in test_code_container.py."""
    monkeypatch.setattr(settings, "CODE_SANDBOX", "process")


@pytest.fixture(autouse=True)
def _disable_auth_rate_limiter():
    """The slowapi auth limiter (RATE_LIMIT_AUTH, 5/min per IP) is keyed on a
    shared client IP across the whole suite, so tests that register/login
    several users contend and randomly 429 depending on run order. Nothing
    asserts this limiter fires (the public-app limiter is separate and tested
    directly), so switch it off for the session."""
    was = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = was
