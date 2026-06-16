"""Polling-trigger Listen-mode driver.

When the editor clicks "Listen" on a Gmail / Calendar trigger node,
the HTTP layer creates a waiting Execution row and opens a
PollingListenSlot. This module's Celery task `poll_listen_slot` then
drives the actual wait: it loops calling the trigger's poller every
few seconds with the cursor we snapshotted at slot open, and the
first event that arrives gets dispatched into the waiting Execution
via `execution_engine.dispatch_existing`.

Lifecycle:

  - Snapshot was taken synchronously in the HTTP handler so the cursor
    is already advanced to "now" before this task starts polling. That
    keeps the wait honest — we only surface events that arrive *after*
    the user clicked Listen, not the backlog.
  - The task polls every `LISTEN_POLL_INTERVAL_SECONDS` (5 s) — much
    faster than the production cadence so the editor feels responsive.
  - Each tick checks the Redis cancel flag first so a cancel click
    short-circuits before the next provider HTTP call.
  - On match: advance the cursor (same transaction that dispatches),
    delete the slot, hand off to `dispatch_existing`.
  - On deadline: mark the Execution `timeout` and publish
    `execution_timeout` so the editor's WS state machine can show
    "Listen window expired".
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime

from apps.api.app.core.celery import celery_app
from apps.api.app.core.logger import get_logger
from apps.api.app.features.triggers.listen_service import close_polling_slot

logger = get_logger(__name__)


LISTEN_POLL_INTERVAL_SECONDS = 5
# Upper bound for exponential backoff between failing ticks. 60 s keeps
# us politely under provider rate-limit reset windows (Gmail 250 quota
# units / user / sec, Calendar 500 / minute) while still giving the
# listen 4–5 retry attempts inside the 5-minute window.
LISTEN_BACKOFF_CAP_SECONDS = 60


@celery_app.task(name="poll_listen_slot")
def poll_listen_slot(
    execution_id: str,
    workflow_id: str,
    node_id: str,
    deadline_iso: str,
) -> None:
    """Entry point Celery hands the task. Wraps `_run` in `asyncio.run`
    because Celery tasks are sync; everything downstream is async."""
    try:
        asyncio.run(_run(execution_id, workflow_id, node_id, deadline_iso))
    except Exception as exc:  # noqa: BLE001
        logger.error(f"poll_listen_slot crashed: {exc}", exc_info=True)


async def _run(
    execution_id: str,
    workflow_id: str,
    node_id: str,
    deadline_iso: str,
) -> None:
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.execution_engine.engine import execution_engine
    from apps.api.app.execution_engine.scheduler.integration_polling import (
        eager_register_polling_providers,
        get_entry_for_provider,
    )
    from apps.api.app.features.credentials.service import CredentialService
    from apps.api.app.features.executions.repository import ExecutionRepository
    from apps.api.app.features.triggers.listen_service import (
        find_polling_slot,
        is_polling_cancelled,
    )
    from apps.api.app.features.triggers.repository import (
        IntegrationTriggerStateRepository,
    )
    from apps.api.app.features.workflows.repository import WorkflowRepository

    # Worker may have come up only running the listen-mode task and
    # never hit the scheduler tick that pulls trigger modules in —
    # without this call `get_entry_for_provider('gdrive')` returns
    # None even though `register_poller("gdrive", ...)` is in the file.
    eager_register_polling_providers()

    try:
        deadline = datetime.fromisoformat(deadline_iso.replace("Z", "+00:00"))
    except ValueError:
        deadline = datetime.now(UTC)

    log_ctx = {
        "execution_id": execution_id,
        "workflow_id": workflow_id,
        "node_id": node_id,
    }
    logger.info(f"poll_listen_slot: started {log_ctx}")

    # Consecutive failing ticks — drives exponential backoff so a
    # provider-side outage doesn't burn through the listen window with
    # 60 wasted retries at 5 s each.
    consecutive_failures = 0
    matched_provider: str | None = None

    while True:
        if datetime.now(UTC) >= deadline:
            await _expire(execution_id)
            return

        if await is_polling_cancelled(workflow_id, node_id):
            # `/listen/cancel` already published execution_cancelled and
            # flipped the row — nothing more to do here.
            return

        slot = await find_polling_slot(workflow_id, node_id)
        if slot is None:
            # Slot vanished (cancel, TTL, or someone else claimed). No
            # progress to report.
            return
        if slot.execution_id != execution_id:
            # A newer Listen click overwrote our slot. Hand off cleanly.
            return

        # One poll iteration — fully self-contained DB session so a
        # transient failure doesn't poison the next tick.
        tick_succeeded = False
        try:
            async with AsyncSessionLocal() as db:
                wf = await WorkflowRepository(db).get_by_id(uuid.UUID(workflow_id))
                if wf is None:
                    await _expire(execution_id, status="failed")
                    return

                entry = get_entry_for_provider(slot.provider)
                if entry is None:
                    logger.warning(
                        "poll_listen_slot: no poller registered for provider %r",
                        slot.provider,
                    )
                    await _expire(execution_id, status="failed")
                    return

                node = _find_node(wf.graph, node_id)
                if node is None:
                    await _expire(execution_id, status="failed")
                    return
                props = (node.get("data") or {}).get("properties") or {}

                cred_service = CredentialService(db)
                token = await _resolve_token(cred_service, slot.credential_id, slot.workspace_id)
                if not token:
                    await _expire(execution_id, status="failed")
                    return

                state_repo = IntegrationTriggerStateRepository(db)
                state = await state_repo.get(wf.id, node_id)
                cursor = state.cursor if state else {}

                matches, new_cursor = await entry.poller(token, cursor, props)
                tick_succeeded = True
                matched_provider = slot.provider

                # Always advance the cursor — even on a no-match tick —
                # so the production scheduler resumes from the same
                # boundary when listen finishes.
                if state is not None:
                    await state_repo.upsert(
                        workflow_id=wf.id,
                        workspace_id=wf.workspace_id,
                        node_id=node_id,
                        provider=slot.provider,
                        cursor=new_cursor,
                        next_poll_at=state.next_poll_at,
                        last_error=None,
                    )
                    await db.commit()

                if matches:
                    # Hand off the first match — Listen is single-shot.
                    payload = matches[0]
                    node_type = str(node.get("type") or "")
                    # Close the slot before dispatching so a retry in
                    # dispatch_existing can't re-fire it.
                    await close_polling_slot(workflow_id, node_id)
                    await execution_engine.dispatch_existing(
                        execution_id=uuid.UUID(execution_id),
                        workflow_id=wf.id,
                        graph=wf.graph,
                        trigger_type=node_type or "listen",
                        input_data=payload,
                    )
                    await _publish(
                        execution_id,
                        {
                            "type": "execution_listen_matched",
                            "execution_id": execution_id,
                            "node_id": node_id,
                            "timestamp": _iso_now(),
                        },
                    )
                    logger.info(f"poll_listen_slot: matched provider={slot.provider} {log_ctx}")
                    await _cleanup_post_listen(
                        workflow_id=workflow_id,
                        node_id=node_id,
                        keep_state=True,  # match dispatched — keep cursor for the run
                    )
                    return
        except Exception as exc:  # noqa: BLE001
            # Don't kill the listen loop on a transient API hiccup;
            # surface to logs and keep polling until deadline.
            logger.warning(f"poll_listen_slot tick failed: {exc} {log_ctx}")

        if tick_succeeded:
            consecutive_failures = 0
        else:
            consecutive_failures += 1

        # Sleep is capped by the remaining deadline so the last tick
        # doesn't oversleep past the timeout window. Exponential backoff
        # kicks in only when the previous tick raised — successful ticks
        # always sleep `LISTEN_POLL_INTERVAL_SECONDS` so a healthy listen
        # stays responsive.
        remaining = (deadline - datetime.now(UTC)).total_seconds()
        if remaining <= 0:
            await _expire(execution_id)
            await _cleanup_post_listen(workflow_id, node_id, keep_state=False)
            return
        base = LISTEN_POLL_INTERVAL_SECONDS * (2 ** min(consecutive_failures, 4))
        sleep_secs = min(LISTEN_BACKOFF_CAP_SECONDS, max(1.0, min(base, remaining)))
        await asyncio.sleep(sleep_secs)

        # Bail if the row was cancelled out from under us between ticks.
        async with AsyncSessionLocal() as db:
            row = await ExecutionRepository(db).get_by_id(uuid.UUID(execution_id))
            if row is None or row.status not in ("waiting",):
                # Either cancelled, timed out by sweeper, or matched by
                # a sibling worker. Either way our work here is done.
                logger.info(
                    f"poll_listen_slot: exit, row status={(row.status if row else None)!r} {log_ctx}"
                )
                # `matched_provider` only sticks when we actually ran a
                # poll in this loop — use it to decide whether the state
                # row is ours to clean up.
                await _cleanup_post_listen(workflow_id, node_id, keep_state=bool(matched_provider))
                return


async def _cleanup_post_listen(
    workflow_id: str,
    node_id: str,
    *,
    keep_state: bool,
) -> None:
    """Drop the `integration_trigger_state` row if the workflow isn't
    active. Keep it when the listen matched (so the workflow's
    just-dispatched execution sees a consistent cursor) and when the
    workflow IS active (the scheduler needs it). Otherwise the user
    listened once and didn't activate — the row would sit idle
    forever, eventually drifting from Google's `historyId` retention
    window."""
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.features.triggers.repository import (
        IntegrationTriggerStateRepository,
    )
    from apps.api.app.features.workflows.repository import WorkflowRepository

    if keep_state:
        return
    try:
        async with AsyncSessionLocal() as db:
            wf = await WorkflowRepository(db).get_by_id(uuid.UUID(workflow_id))
            if wf is None or wf.is_active:
                return
            repo = IntegrationTriggerStateRepository(db)
            await repo.delete(wf.id, node_id)
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"poll_listen_slot post-listen cleanup failed: {exc}")


async def _expire(execution_id: str, status: str = "timeout") -> None:
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.features.executions.repository import ExecutionRepository

    try:
        async with AsyncSessionLocal() as db:
            await ExecutionRepository(db).update_status(uuid.UUID(execution_id), status)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"poll_listen_slot: failed to mark {execution_id} {status}: {exc}")

    await _publish(
        execution_id,
        {
            "type": "execution_timeout" if status == "timeout" else "execution_failed",
            "execution_id": execution_id,
            "status": status,
            "message": (
                "Listen window expired — no event arrived. Try again."
                if status == "timeout"
                else "Listen failed."
            ),
            "timestamp": _iso_now(),
        },
    )


async def _publish(execution_id: str, payload: dict) -> None:
    from apps.api.app.core.redis import get_redis

    try:
        redis = await get_redis()
        await redis.publish(f"execution:{execution_id}", json.dumps(payload))
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"poll_listen_slot pubsub failed for {execution_id}: {exc}")


async def _resolve_token(cred_service, credential_id: str, workspace_id: str) -> str | None:
    if not credential_id or not workspace_id:
        return None
    try:
        cred_uuid = uuid.UUID(credential_id)
        ws_uuid = uuid.UUID(workspace_id)
    except (ValueError, TypeError):
        return None
    cred = await cred_service.repo.get_by_id_and_workspace(cred_uuid, ws_uuid)
    if cred is None:
        return None
    data = await cred_service.get_decrypted_credential(cred)
    if not isinstance(data, dict):
        return None
    token = data.get("access_token")
    return str(token) if isinstance(token, str) else None


def _find_node(graph: dict | None, node_id: str) -> dict | None:
    for node in (graph or {}).get("nodes") or []:
        if isinstance(node, dict) and str(node.get("id") or "") == node_id:
            return node
    return None


def _iso_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
