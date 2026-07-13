"""Rotation-immune spend + concurrency guards for public hosted apps.

The old cost cap summed `session.total_cost_usd` across a source's
sessions, checked at dispatch. An anonymous client mints a fresh session
per request (`POST /session`), so rotating the cookie reset the session
sum to zero and the cap never bit — unbounded LLM spend. And cost was
recorded only *after* the run, so a burst of concurrent messages all
passed the check before any spend landed.

Both are keyed on the SOURCE (workflow/crew) id in Redis, not the
session, so cookie rotation can't reset them:

- ``app_spend:{source_id}:{YYYY-MM-DD}`` — running USD spent today,
  incremented by the worker with the real cost after each run. Read at
  dispatch and compared to the effective daily cap. TTL 2 days.
- ``app_inflight:{source_id}`` — executions dispatched but not yet
  terminal. Incremented at dispatch, decremented by the worker in a
  finally. Bounds the concurrent-burst race the post-hoc cost record
  can't. Self-heals via a short TTL if a worker dies mid-run.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from apps.api.app.core.logger import get_logger
from apps.api.app.core.redis import get_redis

logger = get_logger(__name__)

# In-flight counter TTL: a dead worker that never decrements can't wedge
# an app forever. Comfortably longer than the longest realistic run.
_INFLIGHT_TTL_SECONDS = 60 * 30
_SPEND_TTL_SECONDS = 60 * 60 * 48


def _spend_key(source_id: uuid.UUID | str) -> str:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"app_spend:{source_id}:{today}"


def _inflight_key(source_id: uuid.UUID | str) -> str:
    return f"app_inflight:{source_id}"


async def spend_today(source_id: uuid.UUID | str) -> float:
    """USD spent today for this app. 0.0 if Redis is unavailable (fail
    open on read — the concurrency cap still bounds abuse)."""
    try:
        redis = await get_redis()
        raw = await redis.get(_spend_key(source_id))
        return float(raw) if raw else 0.0
    except Exception as exc:  # noqa: BLE001
        logger.warning("spend_today read failed (%s) — treating as 0", exc)
        return 0.0


async def record_spend(source_id: uuid.UUID | str, usd: float) -> None:
    """Add the real cost of a finished run to today's counter."""
    if usd <= 0:
        return
    try:
        redis = await get_redis()
        key = _spend_key(source_id)
        await redis.incrbyfloat(key, usd)
        await redis.expire(key, _SPEND_TTL_SECONDS)
    except Exception as exc:  # noqa: BLE001
        logger.warning("record_spend failed (%s) — daily cap may undercount", exc)


async def incr_inflight(source_id: uuid.UUID | str) -> int:
    """Register a dispatch. Returns the new in-flight count (1-based)."""
    redis = await get_redis()
    key = _inflight_key(source_id)
    n = await redis.incr(key)
    await redis.expire(key, _INFLIGHT_TTL_SECONDS)
    return int(n)


async def decr_inflight(source_id: uuid.UUID | str) -> None:
    """Release a dispatch when its run reaches a terminal state. Floors at
    0 so a double-decrement (retry) can't drive it negative and starve
    the app."""
    try:
        redis = await get_redis()
        key = _inflight_key(source_id)
        n = await redis.decr(key)
        if n < 0:
            await redis.set(key, 0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("decr_inflight failed (%s)", exc)
