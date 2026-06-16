"""Listen-slot sweeper.

The polling listen loop expects its own Celery task to mark a row
`timeout` when the 5-minute window expires. That's true in the happy
path. If the worker dies mid-listen, or the Redis slot key TTLs out
before the loop's deadline check fires, the `Execution(status="waiting")`
row sits forever. The sweeper closes that loophole.

Runs every minute under Celery beat. Two passes:

  1. Slot pass — scan every `polling:listen:slot:*` key in Redis. If
     its `deadline_iso` is past, close the slot and flip the
     associated execution to `timeout` (idempotent — only flips rows
     still in `waiting`).
  2. Orphan pass — query waiting listen executions whose execution_id
     does NOT appear in any live listen slot (polling or Meta). Those
     rows were stranded by a worker crash or Redis eviction; mark them
     `timeout` so the UI moves on.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from apps.api.app.core.celery import celery_app
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="sweep_polling_listens")
def sweep_polling_listens() -> None:
    try:
        asyncio.run(_sweep())
    except Exception as exc:  # noqa: BLE001
        logger.error(f"sweep_polling_listens crashed: {exc}", exc_info=True)


async def _sweep() -> None:
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.core.redis import get_redis
    from apps.api.app.features.executions.models import Execution
    from apps.api.app.features.executions.repository import ExecutionRepository
    from apps.api.app.features.triggers.listen_service import close_polling_slot

    redis = await get_redis()
    now = datetime.now(UTC)
    live_execution_ids: set[str] = set()

    # ── Pass 1: expire slots past their stored deadline ──────────────
    swept_expired = 0
    async for slot_key in redis.scan_iter(match="polling:listen:slot:*"):
        raw = await redis.get(slot_key)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            deadline = datetime.fromisoformat(
                str(data.get("deadline_iso", "")).replace("Z", "+00:00")
            )
        except (ValueError, json.JSONDecodeError):
            continue
        if now >= deadline:
            execution_id = str(data.get("execution_id") or "")
            workflow_id = str(data.get("workflow_id") or "")
            node_id = str(data.get("node_id") or "")
            if workflow_id and node_id:
                await close_polling_slot(workflow_id, node_id)
            if execution_id:
                await _flip_to_timeout(execution_id)
            swept_expired += 1
        else:
            execution_id = str(data.get("execution_id") or "")
            if execution_id:
                live_execution_ids.add(execution_id)

    # Meta listen slots count as live too — a Meta listen waiting on an
    # event we haven't received yet should NOT be swept as orphaned.
    async for slot_key in redis.scan_iter(match="meta:listen:slot:*"):
        raw = await redis.get(slot_key)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        execution_id = str(data.get("execution_id") or "")
        if execution_id:
            live_execution_ids.add(execution_id)

    # ── Pass 2: orphan recovery ──────────────────────────────────────
    # Executions left stuck in `waiting` with no backing slot. Could be
    # a worker crash mid-listen, a Redis eviction under memory pressure,
    # or a process killed between commit-row + open-slot. Either way the
    # UI is staring at a dead state — flip them to timeout.
    swept_orphans = 0
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Execution).where(
                Execution.status == "waiting",
                Execution.trigger_type == "listen",
            )
        )
        rows = list(result.scalars().all())
        repo = ExecutionRepository(db)
        for row in rows:
            if str(row.id) in live_execution_ids:
                continue
            try:
                await repo.update_status(row.id, "timeout")
                swept_orphans += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"sweep_polling_listens: failed to flip orphan {row.id}: {exc}")
            await _publish_timeout(str(row.id))

    if swept_expired or swept_orphans:
        logger.info(
            "sweep_polling_listens: expired=%d orphans=%d",
            swept_expired,
            swept_orphans,
        )


async def _flip_to_timeout(execution_id: str) -> None:
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.features.executions.models import Execution
    from apps.api.app.features.executions.repository import ExecutionRepository

    try:
        async with AsyncSessionLocal() as db:
            row = (
                await db.execute(select(Execution).where(Execution.id == uuid.UUID(execution_id)))
            ).scalar_one_or_none()
            if row is None or row.status != "waiting":
                return  # already terminal — sweeper is idempotent
            await ExecutionRepository(db).update_status(uuid.UUID(execution_id), "timeout")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"sweep_polling_listens: flip-to-timeout failed for {execution_id}: {exc}")
    await _publish_timeout(execution_id)


async def _publish_timeout(execution_id: str) -> None:
    from apps.api.app.core.redis import get_redis

    try:
        redis = await get_redis()
        await redis.publish(
            f"execution:{execution_id}",
            json.dumps(
                {
                    "type": "execution_timeout",
                    "execution_id": execution_id,
                    "status": "timeout",
                    "message": "Listen window expired — no event arrived. Try again.",
                    "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                }
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"sweep_polling_listens pubsub failed for {execution_id}: {exc}")
