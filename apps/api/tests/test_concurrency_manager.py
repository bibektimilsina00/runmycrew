"""Unit tests for the workflow concurrency mutex.

Uses fakeredis to avoid needing a real Redis in CI. The Lua release
script runs against fakeredis the same way it would against real
Redis (fakeredis supports EVAL).
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import patch

import pytest

from apps.api.app.execution_engine.concurrency import (
    AcquireResult,
    ConcurrencyManager,
    ConcurrencyPolicy,
)


@pytest.fixture
async def fake_redis():
    """Provide a fake Redis client to ConcurrencyManager."""
    import fakeredis.aioredis  # type: ignore[import-not-found]

    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    with patch(
        "apps.api.app.execution_engine.concurrency.get_redis",
        return_value=r,
    ):
        yield r
    await r.aclose()


@pytest.mark.anyio
async def test_acquire_succeeds_when_free(fake_redis):
    mgr = ConcurrencyManager()
    wf = uuid.uuid4()
    result = await mgr.acquire(wf)
    assert result.acquired is True
    assert result.status == "acquired"
    assert result.token is not None


@pytest.mark.anyio
async def test_skip_when_locked(fake_redis):
    mgr = ConcurrencyManager()
    wf = uuid.uuid4()
    first = await mgr.acquire(wf, policy=ConcurrencyPolicy.SKIP)
    second = await mgr.acquire(wf, policy=ConcurrencyPolicy.SKIP)
    assert first.acquired is True
    assert second.acquired is False
    assert second.status == "skipped_concurrent"


@pytest.mark.anyio
async def test_release_only_works_with_own_token(fake_redis):
    mgr = ConcurrencyManager()
    wf = uuid.uuid4()
    held = await mgr.acquire(wf)
    assert held.acquired is True
    # Wrong token must NOT release
    ok = await mgr.release(wf, token="bogus-token")
    assert ok is False
    assert await mgr.is_locked(wf) is True
    # Correct token releases
    ok = await mgr.release(wf, token=held.token)
    assert ok is True
    assert await mgr.is_locked(wf) is False


@pytest.mark.anyio
async def test_release_after_expiry_is_safe(fake_redis):
    mgr = ConcurrencyManager()
    wf = uuid.uuid4()
    held = await mgr.acquire(wf, ttl_seconds=1)
    assert held.acquired is True
    # Wait past TTL — fakeredis honours expirations
    await asyncio.sleep(1.2)
    assert await mgr.is_locked(wf) is False
    # Late release is a no-op (returns False), doesn't raise
    ok = await mgr.release(wf, token=held.token)
    assert ok is False


@pytest.mark.anyio
async def test_replace_forces_acquire(fake_redis):
    mgr = ConcurrencyManager()
    wf = uuid.uuid4()
    first = await mgr.acquire(wf)
    second = await mgr.acquire(wf, policy=ConcurrencyPolicy.REPLACE)
    assert first.acquired is True
    assert second.acquired is True
    assert second.status == "replaced"
    # First holder's release should now fail the CAS guard
    ok = await mgr.release(wf, token=first.token)
    assert ok is False
    # Second holder owns it
    assert await mgr.is_locked(wf) is True
    ok = await mgr.release(wf, token=second.token)
    assert ok is True


@pytest.mark.anyio
async def test_queue_waits_then_acquires(fake_redis):
    mgr = ConcurrencyManager()
    wf = uuid.uuid4()
    held = await mgr.acquire(wf, ttl_seconds=2)
    assert held.acquired is True

    async def waiter() -> AcquireResult:
        return await mgr.acquire(wf, policy=ConcurrencyPolicy.QUEUE, queue_max_wait_seconds=10)

    task = asyncio.create_task(waiter())
    await asyncio.sleep(0.5)
    # Release the original lock — waiter should pick it up
    await mgr.release(wf, token=held.token)
    result = await task
    assert result.acquired is True
    assert result.status == "queued_acquired"
    assert result.waited_seconds > 0


@pytest.mark.anyio
async def test_queue_times_out(fake_redis):
    mgr = ConcurrencyManager()
    wf = uuid.uuid4()
    # Hold for longer than the queue allows
    held = await mgr.acquire(wf, ttl_seconds=60)
    assert held.acquired is True

    result = await mgr.acquire(wf, policy=ConcurrencyPolicy.QUEUE, queue_max_wait_seconds=3)
    assert result.acquired is False
    assert result.status == "queue_timeout"
    assert result.waited_seconds >= 3


@pytest.mark.anyio
async def test_independent_workflows_dont_collide(fake_redis):
    mgr = ConcurrencyManager()
    wf_a = uuid.uuid4()
    wf_b = uuid.uuid4()
    a = await mgr.acquire(wf_a)
    b = await mgr.acquire(wf_b)
    assert a.acquired is True
    assert b.acquired is True


@pytest.fixture
def anyio_backend():
    return "asyncio"
