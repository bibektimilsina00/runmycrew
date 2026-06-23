"""Workflow-level concurrency mutex backed by Redis.

Why: a cron trigger fires every N minutes regardless of whether the
previous run is still in flight. Without a mutex, a slow agent loop
that takes 6 minutes to run on a 5-minute cron quietly overlaps with
itself — duplicate side-effects, double-spend, race conditions on
shared state.

The mutex is **per workflow**, not per worker or per node. Each
workflow can configure its own policy (``skip`` / ``queue`` /
``replace``) under workflow settings.

Lock key shape::

    runmycrew:concurrency:workflow:{workflow_id}

The value is a UUID4 token that the same caller passes back to
``release``. The release script is a Lua atomic CAS so we never
release someone else's lock (e.g. one worker times out mid-run, the
TTL frees the lock, a second worker grabs it, the original worker
finishes and calls release — without the CAS guard it would delete
the second worker's lock).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from apps.api.app.core.redis import get_redis

logger = logging.getLogger(__name__)


LOCK_KEY_PREFIX = "runmycrew:concurrency:workflow:"


class ConcurrencyPolicy(str, Enum):
    """How the mutex should behave when a fire collides with an in-flight run."""

    SKIP = "skip"  # default — drop the new fire, log skipped_concurrent
    QUEUE = "queue"  # wait up to queue_max_wait_seconds, then drop
    REPLACE = "replace"  # force-release + acquire; original run terminates


@dataclass(frozen=True)
class AcquireResult:
    """Outcome of an ``acquire`` call."""

    acquired: bool
    token: str | None  # opaque value to pass back to ``release``
    waited_seconds: float  # how long ``queue`` policy waited before resolving
    status: Literal[
        "acquired", "skipped_concurrent", "queued_acquired", "queue_timeout", "replaced"
    ]


# Lua: only DEL if the key still holds OUR token.
_RELEASE_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
else
    return 0
end
"""

# Lua: atomic check-and-replace — used by the REPLACE policy.
_FORCE_REPLACE_SCRIPT = """
redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[2])
return 1
"""


class ConcurrencyManager:
    """Acquire / release a workflow-scoped mutex.

    Designed to be safe across worker restarts: every acquire sets
    a TTL slightly larger than the workflow's wall-clock budget, so
    a crashed worker's lock auto-expires.

    Default TTL is intentionally generous (1 hour) — workflows
    shorter than that finish and release explicitly; runaway
    workflows are bounded by the agent's own ``max_seconds`` budget.
    """

    DEFAULT_TTL_SECONDS = 60 * 60
    DEFAULT_QUEUE_POLL_INTERVAL = 2.0

    def __init__(self) -> None:
        # Redis client is fetched lazily so the manager is cheap to
        # construct outside an async context (e.g. at import time).
        self._redis = None

    async def _client(self):
        if self._redis is None:
            self._redis = await get_redis()
        return self._redis

    @staticmethod
    def _key(workflow_id: UUID | str) -> str:
        return f"{LOCK_KEY_PREFIX}{workflow_id}"

    async def acquire(
        self,
        workflow_id: UUID | str,
        *,
        policy: ConcurrencyPolicy = ConcurrencyPolicy.SKIP,
        ttl_seconds: int | None = None,
        queue_max_wait_seconds: int = 60,
    ) -> AcquireResult:
        """Try to acquire the workflow mutex.

        Returns ``AcquireResult``. The caller MUST check ``acquired``
        and must call ``release(workflow_id, token)`` exactly once
        for any successful acquire.
        """
        r = await self._client()
        key = self._key(workflow_id)
        token = uuid4().hex
        ttl = int(ttl_seconds or self.DEFAULT_TTL_SECONDS)

        # First try: cheap optimistic acquire.
        ok = await r.set(key, token, ex=ttl, nx=True)
        if ok:
            return AcquireResult(acquired=True, token=token, waited_seconds=0.0, status="acquired")

        # Collision. Branch on policy.
        if policy == ConcurrencyPolicy.SKIP:
            logger.info("concurrency: workflow=%s policy=skip → declined", workflow_id)
            return AcquireResult(
                acquired=False,
                token=None,
                waited_seconds=0.0,
                status="skipped_concurrent",
            )

        if policy == ConcurrencyPolicy.REPLACE:
            # Force the lock onto us. The original holder's eventual
            # release() is a no-op because the CAS will fail.
            await r.eval(_FORCE_REPLACE_SCRIPT, 1, key, token, ttl)
            logger.warning("concurrency: workflow=%s policy=replace → forced", workflow_id)
            return AcquireResult(acquired=True, token=token, waited_seconds=0.0, status="replaced")

        # QUEUE: poll the lock until it frees or we time out.
        elapsed = 0.0
        while elapsed < queue_max_wait_seconds:
            await asyncio.sleep(self.DEFAULT_QUEUE_POLL_INTERVAL)
            elapsed += self.DEFAULT_QUEUE_POLL_INTERVAL
            ok = await r.set(key, token, ex=ttl, nx=True)
            if ok:
                return AcquireResult(
                    acquired=True,
                    token=token,
                    waited_seconds=elapsed,
                    status="queued_acquired",
                )
        logger.info(
            "concurrency: workflow=%s policy=queue → timed out after %.1fs",
            workflow_id,
            elapsed,
        )
        return AcquireResult(
            acquired=False,
            token=None,
            waited_seconds=elapsed,
            status="queue_timeout",
        )

    async def release(self, workflow_id: UUID | str, token: str) -> bool:
        """Release the lock IF we still hold it.

        Returns True if the CAS deleted our entry; False if the lock
        had already expired or been replaced — both safe to ignore.
        """
        if not token:
            return False
        r = await self._client()
        try:
            result = await r.eval(_RELEASE_SCRIPT, 1, self._key(workflow_id), token)
            return bool(result)
        except Exception:
            # Don't surface release errors — the TTL will free the
            # lock anyway. Log and move on.
            logger.exception("concurrency: release failed for workflow=%s", workflow_id)
            return False

    async def is_locked(self, workflow_id: UUID | str) -> bool:
        """Check (without acquiring) whether the workflow is locked.

        Mainly for tests + dashboards.
        """
        r = await self._client()
        return bool(await r.exists(self._key(workflow_id)))
