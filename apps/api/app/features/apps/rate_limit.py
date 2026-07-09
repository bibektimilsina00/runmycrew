"""Redis sliding-window rate limiter for public app endpoints.

Two windows per app:
- per (app_id, session_id) — visitor's own thread
- per (app_id, ip_hash)    — same IP burning cookies

Returns (allowed, retry_after_seconds). Never raises — a Redis failure
falls open so we don't accidentally lock every visitor out on infra hiccups.
"""

from __future__ import annotations

import time
import uuid

from apps.api.app.core.logger import get_logger
from apps.api.app.core.redis import get_redis

logger = get_logger(__name__)


async def check_rate_limit(
    app_id: uuid.UUID,
    session_key: str,
    ip_hash: str | None,
    max_per_minute: int,
) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds).

    Uses a fixed 60s sliding window implemented as a Redis sorted-set of
    timestamps per key. Prunes expired entries on every call.
    """
    if max_per_minute <= 0:
        return True, 0
    try:
        redis = await get_redis()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"rate-limit: redis unavailable — falling open ({exc})")
        return True, 0

    now = time.time()
    cutoff = now - 60.0

    async def _hit(key: str) -> tuple[bool, int]:
        try:
            await redis.zremrangebyscore(key, "-inf", cutoff)
            count = await redis.zcard(key)
            if count >= max_per_minute:
                oldest = await redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    _, score = oldest[0]
                    retry = max(1, int(60 - (now - float(score))))
                else:
                    retry = 60
                return False, retry
            await redis.zadd(key, {f"{now}-{uuid.uuid4().hex[:8]}": now})
            await redis.expire(key, 90)
            return True, 0
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"rate-limit: check failed ({exc}) — falling open")
            return True, 0

    ok_s, retry_s = await _hit(f"app_rl:s:{app_id}:{session_key}")
    if not ok_s:
        return False, retry_s
    if ip_hash:
        ok_i, retry_i = await _hit(f"app_rl:i:{app_id}:{ip_hash}")
        if not ok_i:
            return False, retry_i
    return True, 0
