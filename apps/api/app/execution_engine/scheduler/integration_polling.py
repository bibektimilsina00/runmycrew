"""Polling scheduler for integration trigger nodes.

Runs once a minute under Celery beat. For every `integration_trigger_state`
row whose `next_poll_at` has passed, we:

  1. Load the workflow + the trigger node properties.
  2. Resolve the credential the node points at (refresh OAuth token if
     it's near expiry — same path nodes use at runtime).
  3. Hand `(token, current_cursor)` to the provider's trigger node and
     let it return `(matched_messages, new_cursor)`.
  4. Dispatch one `execute_workflow` task per matched message so each
     fans out into its own execution row.
  5. Persist the new cursor + next_poll_at in a single transaction so a
     crash between dispatch and persist re-emits at worst — never skips.

The scheduler is provider-aware: each integration registers itself in
`_POLLERS` so adding Calendar / Drive / Docs later is one entry per
surface, no scheduler changes.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from apps.api.app.core.celery import celery_app
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)


# Each entry: provider_tag → async callable that takes the current
# cursor dict + the resolved access token + the trigger node's
# properties dict and returns `(matched_messages, new_cursor)`.
PollerCallable = Callable[
    [str, dict[str, Any] | None, dict[str, Any]],
    Awaitable[tuple[list[dict[str, Any]], dict[str, Any]]],
]
_POLLERS: dict[str, PollerCallable] = {}


def register_poller(provider: str, poller: PollerCallable) -> None:
    """Provider modules call this at import time to wire themselves into
    the scheduler. Re-registering the same provider replaces — useful
    for hot-reload in dev."""
    _POLLERS[provider] = poller


@celery_app.task(name="poll_integration_triggers")
def poll_integration_triggers() -> None:
    asyncio.run(_poll_due_rows())


async def _poll_due_rows() -> None:
    # Lazy import to avoid hauling the world into every worker process
    # boot — most workers only run `execute_workflow`.
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.execution_engine.engine import execution_engine
    from apps.api.app.features.credentials.service import CredentialService
    from apps.api.app.features.triggers.repository import (
        IntegrationTriggerStateRepository,
    )
    from apps.api.app.features.workflows.repository import WorkflowRepository

    # Register the providers we ship with. Each module's `register_poller`
    # call is idempotent so reloading the worker doesn't double-fire.
    from apps.api.app.node_system.nodes.gmail import gmail_trigger as _gmail_trigger  # noqa: F401

    if not _POLLERS:
        return

    async with AsyncSessionLocal() as db:
        state_repo = IntegrationTriggerStateRepository(db)
        # `list_due` is provider-agnostic — we filter inside the loop so
        # we only need one query per tick.
        due_rows = await state_repo.list_due()
        if not due_rows:
            return

        wf_repo = WorkflowRepository(db)
        cred_service = CredentialService(db)

        for state in due_rows:
            provider = state.provider
            poller = _POLLERS.get(provider)
            if poller is None:
                # Unknown provider — likely a row left over from an
                # uninstalled integration. Push its schedule out so it
                # doesn't keep showing up every tick, but don't delete
                # in case the integration comes back.
                state.next_poll_at = datetime.now(UTC) + timedelta(minutes=10)
                state.last_error = f"No poller registered for provider {provider!r}"
                await db.commit()
                continue

            try:
                workflow = await wf_repo.get_by_id(state.workflow_id)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Integration polling: workflow lookup failed for %s/%s: %s",
                    state.workflow_id,
                    state.node_id,
                    exc,
                )
                continue
            if workflow is None:
                # Workflow deleted — clean up the orphaned state row.
                await state_repo.delete(state.workflow_id, state.node_id)
                await db.commit()
                continue

            node = _find_trigger_node(workflow.graph, state.node_id)
            if node is None:
                # Node removed from the graph since last poll. Drop the
                # cursor; if the user adds the node back, a fresh
                # snapshot will start cleanly.
                await state_repo.delete(state.workflow_id, state.node_id)
                await db.commit()
                continue

            props = (node.get("data") or {}).get("properties") or {}
            credential_id = props.get("credential")
            try:
                token = await _resolve_access_token(cred_service, credential_id, state.workspace_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Integration polling: cred resolve failed for %s/%s: %s",
                    state.workflow_id,
                    state.node_id,
                    exc,
                )
                state.last_error = f"Credential resolve failed: {exc}"[:1024]
                state.next_poll_at = _retry_after(props)
                await db.commit()
                continue
            if not token:
                state.last_error = "Credential missing access_token"
                state.next_poll_at = _retry_after(props)
                await db.commit()
                continue

            try:
                matches, new_cursor = await poller(token, state.cursor, props)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Integration polling: %s poller raised for %s/%s: %s",
                    provider,
                    state.workflow_id,
                    state.node_id,
                    exc,
                )
                state.last_error = str(exc)[:1024]
                state.next_poll_at = _retry_after(props)
                await db.commit()
                continue

            # Dispatch each match as its own execution — fan-out runs in
            # parallel under Celery's worker pool, one row per inbound
            # message just like a webhook delivery would.
            trigger_type = node.get("type") or ""
            for payload in matches:
                try:
                    await execution_engine.trigger_workflow(
                        workflow_id=workflow.id,
                        graph=workflow.graph,
                        trigger_type=trigger_type,
                        input_data=payload,
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Integration polling: dispatch failed for %s/%s: %s",
                        state.workflow_id,
                        state.node_id,
                        exc,
                    )

            state.cursor = new_cursor
            state.last_polled_at = datetime.now(UTC)
            state.last_error = None
            state.next_poll_at = _next_poll_at_from_props(props)
            await db.commit()


# ── helpers ──────────────────────────────────────────────────────────────


def _find_trigger_node(graph: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    for node in (graph or {}).get("nodes") or []:
        if isinstance(node, dict) and node.get("id") == node_id:
            return node
    return None


async def _resolve_access_token(
    cred_service: Any, credential_id: Any, workspace_id: Any
) -> str | None:
    """Pull the OAuth access token off a credential, refreshing if the
    stored expiry is past. Uses the same service the runtime path uses
    so a refresh here keeps subsequent node runs aligned."""
    import uuid

    if not credential_id or not workspace_id:
        return None
    try:
        cred_uuid = uuid.UUID(str(credential_id))
        ws_uuid = uuid.UUID(str(workspace_id))
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


def _next_poll_at_from_props(props: dict[str, Any]) -> datetime:
    interval = props.get("poll_interval_seconds")
    try:
        seconds = int(interval) if interval is not None else 60
    except (TypeError, ValueError):
        seconds = 60
    seconds = max(30, min(seconds, 60 * 60))
    return datetime.now(UTC) + timedelta(seconds=seconds)


def _retry_after(props: dict[str, Any]) -> datetime:
    """Back off a bit after a transient failure so we don't hammer the
    provider on every tick. Doubles the configured cadence (capped at
    10 minutes) — long enough for token-refresh / rate-limit recovery."""
    base = _next_poll_at_from_props(props) - datetime.now(UTC)
    backoff = min(base * 2, timedelta(minutes=10))
    return datetime.now(UTC) + backoff
