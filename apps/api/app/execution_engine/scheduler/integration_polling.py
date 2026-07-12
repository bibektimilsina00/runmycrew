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


# Each registered poller binds three things:
#   - the node `type` string (e.g. `trigger.gmail`) the workflow graph
#     emits — so the workflow service can decide which nodes need a
#     cursor row on save.
#   - the `provider` tag persisted on `integration_trigger_state.provider`
#     so we can route a stored row back to a poller after a worker
#     restart.
#   - the async poller callable.
PollerCallable = Callable[
    [str, dict[str, Any] | None, dict[str, Any]],
    Awaitable[tuple[list[dict[str, Any]], dict[str, Any]]],
]


class PollerEntry:
    __slots__ = ("node_type", "provider", "poller", "token_fields")

    def __init__(
        self,
        node_type: str,
        provider: str,
        poller: PollerCallable,
        token_fields: list[str] | None = None,
    ) -> None:
        self.node_type = node_type
        self.provider = provider
        self.poller = poller
        # Ordered list of credential dict keys to try when the scheduler
        # pulls a token to hand to the poller. Defaults to `access_token`
        # only, which works for every OAuth provider — API-key providers
        # (GitLab, Trello, Klaviyo, PagerDuty) override with the field
        # their credential type actually persists.
        # `token_fields=[]` (explicit empty list) marks the provider as
        # unauthenticated — scheduler runs the poller with an empty
        # token and skips the credential lookup entirely. `None` still
        # falls through to the OAuth default.
        self.token_fields = list(token_fields) if token_fields is not None else ["access_token"]


_BY_NODE_TYPE: dict[str, PollerEntry] = {}
_BY_PROVIDER: dict[str, PollerEntry] = {}


def register_poller(
    *,
    node_type: str,
    provider: str,
    poller: PollerCallable,
    token_fields: list[str] | None = None,
) -> None:
    """Provider modules call this at import time to wire themselves into
    the scheduler. Re-registering the same `node_type` replaces — useful
    for hot-reload in dev.

    `token_fields` names the credential keys the scheduler should try, in
    order, when extracting the value to hand to the poller. Defaults to
    `['access_token']` for OAuth."""
    entry = PollerEntry(
        node_type=node_type,
        provider=provider,
        poller=poller,
        token_fields=token_fields,
    )
    _BY_NODE_TYPE[node_type] = entry
    _BY_PROVIDER[provider] = entry


def get_entry_for_node_type(node_type: str) -> PollerEntry | None:
    return _BY_NODE_TYPE.get(node_type)


def get_entry_for_provider(provider: str) -> PollerEntry | None:
    return _BY_PROVIDER.get(provider)


def eager_register_polling_providers() -> None:
    """Import every polling-trigger module so its module-scope
    `register_poller(...)` has fired before the first scheduler or
    listener tick. Idempotent — re-imports are no-ops, re-registrations
    overwrite with the same entry.

    Adding a new polling integration means one extra line here. Calling
    from both `_poll_due_rows` (scheduler tick) and the listen-mode
    Celery task means a worker that only ever runs one of those paths
    still sees the right providers."""
    # Phase 3.1 — dev/CRM polling triggers.
    from apps.api.app.node_system.nodes.asana import (
        asana_trigger as _asana_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.ashby import (
        ashby_trigger as _ashby_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.atlassian.confluence import (
        confluence_trigger as _confluence_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.atlassian.jira import (
        jira_trigger as _jira_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.atlassian.trello import (
        trello_trigger as _trello_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.attio import (
        attio_trigger as _attio_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.calcom import (
        calcom_trigger as _calcom_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.calendly import (
        calendly_trigger as _calendly_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.emailbison import (
        emailbison_trigger as _emailbison_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.gitlab import (
        gitlab_trigger as _gitlab_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.google.gcalendar import (
        gcal_trigger as _gcal_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.google.gchat import (
        gchat_trigger as _gchat_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.google.gdrive import (
        gdrive_trigger as _gdrive_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.google.gforms import (
        gforms_trigger as _gforms_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.google.gmail import (
        gmail_trigger as _gmail_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.google.google_sheets import (
        google_sheets_trigger as _google_sheets_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.google.gpeople import (
        gpeople_trigger as _gpeople_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.google.gtasks import (
        gtasks_trigger as _gtasks_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.google.gyt import (
        gyt_trigger as _gyt_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.grain import (
        grain_trigger as _grain_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.greenhouse import (
        greenhouse_trigger as _greenhouse_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.hubspot import (
        hubspot_trigger as _hubspot_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.imap import (
        imap_trigger as _imap_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.instantly import (
        instantly_trigger as _instantly_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.intercom import (
        intercom_trigger as _intercom_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.lemlist import (
        lemlist_trigger as _lemlist_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.linear import (
        linear_trigger as _linear_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.microsoft.outlook import (
        outlook_trigger as _outlook_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.monday import (
        monday_trigger as _monday_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.notion import (
        notion_trigger as _notion_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.pagerduty import (
        pagerduty_trigger as _pagerduty_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.rss import (
        rss_trigger as _rss_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.salesforce import (
        salesforce_trigger as _salesforce_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.servicenow import (
        servicenow_trigger as _servicenow_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.telegram import (
        telegram_trigger as _telegram_trigger,  # noqa: F401
    )
    from apps.api.app.node_system.nodes.zendesk import (
        zendesk_trigger as _zendesk_trigger,  # noqa: F401
    )

    # Canary: the register_poller back-import inside the polling factory
    # swallows failures (circular imports silently killed 28/36 pollers in
    # July 2026). If registrations ever drop below the known floor, scream.
    _MIN_EXPECTED_POLLERS = 30
    if len(_BY_PROVIDER) < _MIN_EXPECTED_POLLERS:
        logger.error(
            f"Only {len(_BY_PROVIDER)} polling providers registered "
            f"(expected >= {_MIN_EXPECTED_POLLERS}) — check for import-order "
            f"failures in polling_node_factory registrations."
        )


@celery_app.task(name="poll_integration_triggers")
def poll_integration_triggers() -> None:
    asyncio.run(_poll_due_rows())


async def _poll_due_rows() -> None:
    # Lazy import to avoid hauling the world into every worker process
    # boot — most workers only run `execute_workflow`.
    from apps.api.app.core.database import AsyncSessionLocal
    from apps.api.app.execution_engine.engine import execution_engine
    from apps.api.app.features.credentials.service import CredentialService
    from apps.api.app.features.triggers.listen_service import is_polling_listen_active
    from apps.api.app.features.triggers.repository import (
        IntegrationTriggerStateRepository,
    )
    from apps.api.app.features.workflows.repository import WorkflowRepository

    # Make sure every polling-trigger module has its `_register()` call
    # in the worker's process before we hit `_BY_PROVIDER`.
    eager_register_polling_providers()

    if not _BY_PROVIDER:
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
            # Skip rows whose user is actively listening — the listen
            # loop owns the cursor for its window. Otherwise both loops
            # race for the same delta and the scheduler can grab the
            # event the user is testing, leaving the listen UI hanging.
            if await is_polling_listen_active(str(state.workflow_id), state.node_id):
                # Push the row's next_poll_at past the listen TTL so we
                # don't spin on it every tick during the wait.
                state.next_poll_at = datetime.now(UTC) + timedelta(minutes=6)
                await db.commit()
                continue

            provider = state.provider
            entry = _BY_PROVIDER.get(provider)
            if entry is None:
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
            if not workflow.is_active:
                # User paused the workflow between save and beat tick.
                # Drop the row; re-activation will re-seed a snapshot.
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
            if not entry.token_fields:
                # Unauthenticated provider (RSS) — registered with an
                # empty token_fields list. Poller runs with an empty
                # token and doesn't touch the cred service.
                token = ""
            else:
                try:
                    token = await _resolve_access_token(
                        cred_service,
                        credential_id,
                        state.workspace_id,
                        token_fields=entry.token_fields,
                    )
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
                matches, new_cursor = await entry.poller(token, state.cursor, props)
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
    cred_service: Any,
    credential_id: Any,
    workspace_id: Any,
    *,
    token_fields: list[str] | None = None,
) -> str | None:
    """Pull the auth token off a credential, refreshing if the stored
    expiry is past. Uses the same service the runtime path uses so a
    refresh here keeps subsequent node runs aligned.

    `token_fields` is an ordered list of credential-dict keys to try —
    OAuth providers use `['access_token']`, API-key ones override with
    `['api_key']` or similar. Falling through both keeps mixed-auth
    providers (HubSpot supports OAuth or an api_key) working."""
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
    for key in token_fields or ["access_token"]:
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return None


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
