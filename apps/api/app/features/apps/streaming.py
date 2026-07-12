"""SSE stream helper for the public chat endpoint.

Subscribes to the Redis pub/sub channel a workflow execution writes to
(``execution:{id}``), forwards each event as an SSE frame, and closes the
connection once the runtime emits ``execution_completed`` /
``execution_failed`` / ``execution_cancelled``.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from apps.api.app.core.logger import get_logger
from apps.api.app.core.redis import get_redis

logger = get_logger(__name__)

# Events that signal the SSE stream should terminate.
TERMINAL_EVENTS = {
    "execution_completed",
    "execution_failed",
    "execution_cancelled",
    "execution_paused",
    "stream_end",
}


def _sse_frame(event: str, data: dict[str, Any]) -> str:
    """Format a single SSE frame with event name + JSON payload."""
    payload = json.dumps(data, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


async def stream_execution_events(
    execution_id: str, timeout_s: float = 300.0
) -> AsyncGenerator[str]:
    """Yield SSE-encoded strings for one execution.

    Auto-terminates on any TERMINAL_EVENTS or after ``timeout_s`` idle.
    Heartbeats every 20s so proxies don't close the connection mid-run.
    """
    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = f"execution:{execution_id}"
    await pubsub.subscribe(channel)

    # Optimistic hello so clients see the connection is live before any
    # real events arrive.
    yield _sse_frame(
        "stream_open",
        {"execution_id": execution_id, "channel": channel},
    )

    idle_deadline = timeout_s
    heartbeat_every = 20.0
    started_at = asyncio.get_event_loop().time()
    last_beat = started_at

    try:
        while True:
            now = asyncio.get_event_loop().time()
            if now - started_at > idle_deadline:
                yield _sse_frame("stream_end", {"reason": "timeout", "execution_id": execution_id})
                return
            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg is None:
                # heartbeat
                if now - last_beat > heartbeat_every:
                    yield ": ping\n\n"
                    last_beat = now
                continue

            data = msg.get("data")
            if isinstance(data, bytes | bytearray):
                data = data.decode("utf-8", errors="replace")
            try:
                parsed = json.loads(data) if isinstance(data, str) else {}
            except json.JSONDecodeError:
                continue

            event_type = parsed.get("type") or "message"
            yield _sse_frame(event_type, parsed)

            if event_type in TERMINAL_EVENTS:
                yield _sse_frame("stream_end", {"reason": event_type, "execution_id": execution_id})
                return

            # Bump idle deadline slightly on activity so quiet streams still
            # bail but chatty ones don't get killed prematurely.
            started_at = now
    except asyncio.CancelledError:
        # Client disconnected — normal shutdown path
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"SSE stream error for execution {execution_id}: {exc}")
        yield _sse_frame("error", {"error": str(exc)})
    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
        except Exception:  # noqa: BLE001
            # Cleanup on an already-dead connection — nothing to report.
            pass
