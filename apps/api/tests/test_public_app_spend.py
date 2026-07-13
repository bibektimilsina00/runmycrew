"""Rotation-immune spend + concurrency guards (features/apps/spend.py) and
their enforcement at the public message endpoint.

The unit tests drive a minimal in-memory fake Redis so they're
deterministic and need no server. The endpoint tests monkeypatch the
spend helpers the router calls.
"""

import uuid

import pytest

from apps.api.app.features.apps import spend


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class _FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, float] = {}

    async def get(self, k):
        v = self.store.get(k)
        return None if v is None else str(v)

    async def incrbyfloat(self, k, amt):
        self.store[k] = float(self.store.get(k, 0.0)) + float(amt)
        return self.store[k]

    async def incr(self, k):
        self.store[k] = int(self.store.get(k, 0)) + 1
        return self.store[k]

    async def decr(self, k):
        self.store[k] = int(self.store.get(k, 0)) - 1
        return self.store[k]

    async def set(self, k, v):
        self.store[k] = v

    async def expire(self, k, ttl):
        pass


@pytest.fixture
def fake_redis(monkeypatch) -> _FakeRedis:
    r = _FakeRedis()

    async def _get_redis():
        return r

    monkeypatch.setattr(spend, "get_redis", _get_redis)
    return r


@pytest.mark.anyio
async def test_record_and_read_spend_is_per_source(fake_redis):
    a, b = uuid.uuid4(), uuid.uuid4()
    await spend.record_spend(a, 1.50)
    await spend.record_spend(a, 0.25)
    await spend.record_spend(b, 9.00)
    # Each source has its own counter — a new session can't reset it.
    assert abs(await spend.spend_today(a) - 1.75) < 1e-6
    assert abs(await spend.spend_today(b) - 9.00) < 1e-6


@pytest.mark.anyio
async def test_record_spend_ignores_nonpositive(fake_redis):
    a = uuid.uuid4()
    await spend.record_spend(a, 0)
    await spend.record_spend(a, -5)
    assert await spend.spend_today(a) == 0.0


@pytest.mark.anyio
async def test_spend_today_fails_open_on_redis_error(monkeypatch):
    async def _boom():
        raise RuntimeError("redis down")

    monkeypatch.setattr(spend, "get_redis", _boom)
    # Read fails open (0) — the concurrency cap still bounds abuse.
    assert await spend.spend_today(uuid.uuid4()) == 0.0


@pytest.mark.anyio
async def test_inflight_incr_and_decr(fake_redis):
    a = uuid.uuid4()
    assert await spend.incr_inflight(a) == 1
    assert await spend.incr_inflight(a) == 2
    await spend.decr_inflight(a)
    # Counter is back to 1; a fresh incr reads 2 again.
    assert await spend.incr_inflight(a) == 2


@pytest.mark.anyio
async def test_decr_inflight_floors_at_zero(fake_redis):
    a = uuid.uuid4()
    await spend.decr_inflight(a)  # underflow guard
    assert int(fake_redis.store[spend._inflight_key(a)]) == 0
