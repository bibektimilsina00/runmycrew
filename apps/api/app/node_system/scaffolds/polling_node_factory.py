"""Build a polling-trigger `BaseNode` from a `PollingTriggerManifest`.

The factory mirrors the architecture of `rest_node_factory.py`:

1. **Property model synthesis** — `event_type` enum + every common
   field + the shared `max_per_poll` / `poll_interval_seconds`.
2. **Inspector schema** — credential row, event dropdown, then each
   common field (gated by `extra_fields` membership when appropriate).
3. **Dispatch** — `execute()` performs:
     a. credential + scope resolution
     b. cursor load from `integration_trigger_state`
     c. paginated GET against `event.list_path`
     d. cursor diff (builtin or custom)
     e. cursor upsert + commit
     f. return first match (rest fan out via scheduler tasks)
4. **Scheduler bind** — `_poll_for_scheduler` + `register_poller`
   wired automatically so the worker picks up the trigger after
   restart.

The factory also exposes a stateless preview path for the editor's
`/listen` flow — first-poll snapshots silently in the persistent path,
but the preview primes the cursor so the user can see one match in the
editor.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, create_model

from apps.api.app.core.logger import get_logger
from apps.api.app.features.triggers.repository import IntegrationTriggerStateRepository
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template
from apps.api.app.node_system.scaffolds.polling_cursor import (
    diff_known_ids,
    diff_last_sha,
    diff_since_timestamp,
)
from apps.api.app.node_system.scaffolds.polling_manifest import (
    PollingEvent,
    PollingTriggerManifest,
)
from apps.api.app.node_system.scaffolds.rest_dispatch import build_auth, get_flatten

logger = get_logger(__name__)


_TYPE_ANNOTATIONS: dict[str, Any] = {
    "string": str | None,
    "number": float | None,
    "boolean": bool | None,
    "options": str | None,
    "credential": str | None,
    "json": Any,
}


def _safe_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _synth_polling_props(manifest: PollingTriggerManifest) -> type[BaseModel]:
    """Pydantic model: `credential`, `event_type`, every common field,
    plus `max_per_poll` / `poll_interval_seconds`."""
    defs: dict[str, tuple[Any, Any]] = {
        "credential": (str | None, None),
        "event_type": (str, manifest.events[0].id if manifest.events else ""),
        "max_per_poll": (int, 25),
        "poll_interval_seconds": (int, manifest.default_poll_interval_seconds),
    }
    for field in manifest.common_fields:
        if field.name in defs:
            continue
        defs[field.name] = (_TYPE_ANNOTATIONS.get(field.type, Any), field.default)
    return create_model(
        f"{manifest.name.replace(' ', '')}TriggerProperties",
        __config__=ConfigDict(extra="ignore"),
        **defs,
    )


def _build_polling_schema(manifest: PollingTriggerManifest) -> list[dict[str, Any]]:
    """Inspector schema = credential + event_type + common_fields +
    advanced max_per_poll / poll_interval_seconds."""
    schema: list[dict[str, Any]] = []

    cred_row: dict[str, Any] = {
        "name": "credential",
        "label": f"{manifest.name} Account",
        "type": "credential",
        "credentialType": manifest.credential_type,
        "required": True,
    }
    schema.append(cred_row)

    schema.append(
        {
            "name": "event_type",
            "label": "Event",
            "type": "options",
            "default": manifest.events[0].id if manifest.events else "",
            "options": [{"label": e.label, "value": e.id} for e in manifest.events],
        }
    )

    # Per-common-field visibility — derived from each event's
    # `extra_fields` list (mirror of REST's `visible_fields`). A field
    # absent from every event stays unconditional.
    visibility: dict[str, list[str]] = {}
    for event in manifest.events:
        for fname in event.extra_fields:
            visibility.setdefault(fname, []).append(event.id)

    for field in manifest.common_fields:
        row = field.to_inspector_dict()
        if "condition" not in row:
            event_ids = visibility.get(field.name)
            if event_ids:
                row["condition"] = {"field": "event_type", "value": event_ids}
        schema.append(row)

    schema.append(
        {
            "name": "max_per_poll",
            "label": "Max events per poll",
            "type": "number",
            "default": 25,
            "mode": "advanced",
        }
    )
    schema.append(
        {
            "name": "poll_interval_seconds",
            "label": "Poll interval (seconds)",
            "type": "number",
            "default": manifest.default_poll_interval_seconds,
            "description": (
                f"Min {manifest.min_poll_interval_seconds}s, "
                f"max {manifest.max_poll_interval_seconds}s."
            ),
            "mode": "advanced",
        }
    )
    return schema


def _resolve_token(node: Any, manifest: PollingTriggerManifest) -> str | None:
    if not node.credential:
        return None
    candidates = manifest.token_field
    keys = candidates if isinstance(candidates, list) else [candidates]
    for key in keys:
        value = node.credential.get(key)
        if value:
            return str(value)
    return None


def _next_poll_at(interval: int, manifest: PollingTriggerManifest) -> datetime:
    seconds = max(
        manifest.min_poll_interval_seconds,
        min(
            int(interval or manifest.default_poll_interval_seconds),
            manifest.max_poll_interval_seconds,
        ),
    )
    return datetime.now(UTC) + timedelta(seconds=seconds)


def _scope_dict(manifest: PollingTriggerManifest, props: Any) -> dict[str, Any]:
    """Identity keys baked into every cursor — lets diff strategies
    detect a scope change (e.g. owner/repo swap) and reset.

    Default: every `common_fields` value that's a non-empty string.
    Numbers / bools are excluded to keep the cursor key set stable.
    """
    out: dict[str, Any] = {}
    for field in manifest.common_fields:
        v = getattr(props, field.name, None)
        if isinstance(v, str) and v:
            out[field.name] = v
    return out


async def _fetch_single_page(
    client: httpx.AsyncClient,
    *,
    manifest: PollingTriggerManifest,
    event: PollingEvent,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Default fetcher — one GET, return the items list.

    Walks the manifest auth scheme and the event's `list_path` (template).
    Subclasses with multi-page or RSS-style endpoints set
    `manifest.paginate_fn` instead.
    """
    url = manifest.base_url + resolve_template(event.list_path, props)
    headers_extra, params_extra = build_auth(
        token=token,
        scheme=manifest.auth,
        header_name=manifest.auth_header_name,
        value_template=manifest.auth_value_template,
        query_param=manifest.auth_query_param,
    )
    headers = {"Accept": "application/json", **manifest.extra_headers, **headers_extra}
    # Resolve list_params templates too, so the manifest can write
    # `{"maxResults": "{max_per_poll}"}`-style values.
    resolved_params = {
        k: (resolve_template(v, props) if isinstance(v, str) else v)
        for k, v in event.list_params.items()
    }
    combined_params = {**params_extra, **resolved_params}
    resp = await client.get(
        url,
        headers=headers,
        params=combined_params or None,
        timeout=manifest.timeout_seconds,
    )
    resp.raise_for_status()
    body = resp.json()
    if isinstance(body, dict):
        # Heuristic: most providers wrap items under `items` /
        # `value` / `results` / `data`. Manifests that need a custom
        # extraction key should pass `paginate_fn`.
        for key in ("items", "results", "data", "value", "issues", "pulls", "comments"):
            if isinstance(body.get(key), list):
                return body[key]
        return []
    if isinstance(body, list):
        return body
    return []


def _diff_for_event(
    event: PollingEvent,
    items: list[dict[str, Any]],
    cursor: dict[str, Any] | None,
    props: Any,
    scope: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Dispatch to the right diff function for this event."""
    flatten_fn = get_flatten(event.flatten)

    if event.diff_handler is not None:
        return event.diff_handler(items, cursor, props, event.id)

    if event.strategy == "known_ids":
        return diff_known_ids(
            items,
            cursor,
            id_field=event.id_field,
            flatten_fn=flatten_fn,
            event_id=event.id,
            props=props,
            scope=scope,
        )
    if event.strategy == "since_timestamp":
        return diff_since_timestamp(
            items,
            cursor,
            timestamp_field=event.timestamp_field,
            flatten_fn=flatten_fn,
            event_id=event.id,
            props=props,
            scope=scope,
        )
    if event.strategy == "last_sha":
        return diff_last_sha(
            items,
            cursor,
            flatten_fn=flatten_fn,
            event_id=event.id,
            props=props,
            scope=scope,
        )
    # Unknown strategy — return empty match list with primed cursor.
    return [], {"event_type": event.id, **scope}


def _cursor_summary(cursor: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"event_type": cursor.get("event_type")}
    if "known_ids" in cursor:
        summary["tracked_ids"] = len(cursor.get("known_ids") or [])
    if "since" in cursor:
        summary["since"] = cursor.get("since")
    if "etags" in cursor and isinstance(cursor["etags"], dict):
        summary["tracked_etags"] = len(cursor["etags"])
    return summary


def build_polling_trigger(manifest: PollingTriggerManifest) -> type[BaseNode]:
    """Build a registered-style polling-trigger `BaseNode` subclass."""
    Props = _synth_polling_props(manifest)
    schema = _build_polling_schema(manifest)
    event_index: dict[str, PollingEvent] = {e.id: e for e in manifest.events}
    event_ids = tuple(event_index.keys())

    metadata = NodeMetadata(
        type=manifest.type,
        name=manifest.name,
        category=manifest.category,
        description=manifest.description,
        properties=schema,
        inputs=0,
        outputs=1,
        icon=manifest.icon_slug or "Circle",
        color=manifest.color,
        outputs_schema=manifest.outputs_schema,
        allow_error=True,
        credential_type=manifest.credential_type,
    )

    async def _run_poll(
        node: Any,
        token: str,
        cursor: dict[str, Any] | None,
        client: httpx.AsyncClient,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        event_id = getattr(node.props, "event_type", None) or (event_ids[0] if event_ids else "")
        event = event_index.get(event_id)
        if event is None:
            return [], {"event_type": event_id}

        scope = _scope_dict(manifest, node.props)
        # Reset on event swap or scope change — keeps stale ids/etags
        # from silencing the next poll.
        if cursor:
            prior_event = cursor.get("event_type")
            prior_scope = {k: cursor.get(k) for k in scope}
            if prior_event != event_id or prior_scope != scope:
                cursor = None

        fetcher = manifest.paginate_fn or _fetch_single_page
        items = await fetcher(
            client,
            manifest=manifest,
            event=event,
            token=token,
            props=node.props,
        )
        if event.filter_fn is not None:
            items = [it for it in items if event.filter_fn(it, node.props)]
        return _diff_for_event(event, items, cursor, node.props, scope)

    class _ManifestTriggerNode(BaseNode[Props]):  # type: ignore[valid-type]
        _manifest = manifest

        @classmethod
        def get_properties_model(cls) -> type[BaseModel]:
            return Props

        @classmethod
        def get_metadata(cls) -> NodeMetadata:
            return metadata

        async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
            # Scheduler hands us the matched event payload directly.
            if (
                isinstance(input_data, dict)
                and input_data.get("event_type") in event_ids
                and any(input_data.get(k) for k in ("id", "sha", "number", "resource_name"))
            ):
                return NodeResult(success=True, output_data=input_data)

            token = _resolve_token(self, manifest)
            if not token:
                return NodeResult(success=False, error=f"{manifest.name} credential required.")

            wf_id = _safe_uuid(getattr(context, "workflow_id", None))
            ws_id = _safe_uuid(getattr(context, "workspace_id", None))
            node_id = getattr(context, "node_id", None)
            db = getattr(context, "db", None)

            if wf_id is None or ws_id is None or db is None or not node_id:
                return await self._stateless_preview(token)

            repo = IntegrationTriggerStateRepository(db)
            state = await repo.get(wf_id, node_id)
            cursor = state.cursor if state else None

            try:
                async with httpx.AsyncClient(timeout=manifest.timeout_seconds) as client:
                    matches, new_cursor = await _run_poll(self, token, cursor, client)
            except httpx.HTTPStatusError as exc:
                return NodeResult(
                    success=False,
                    error=f"{manifest.name} API error {exc.response.status_code}: "
                    f"{exc.response.text[:200]}",
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("%s poll failed: %s", manifest.type, exc, exc_info=True)
                return NodeResult(success=False, error=str(exc))

            await repo.upsert(
                workflow_id=wf_id,
                workspace_id=ws_id,
                node_id=node_id,
                provider=manifest.provider,
                cursor=new_cursor,
                next_poll_at=_next_poll_at(self.props.poll_interval_seconds, manifest),
                last_error=None,
            )
            await db.commit()

            if not matches:
                return NodeResult(
                    success=True,
                    output_data={
                        "matched": 0,
                        "items": [],
                        **_cursor_summary(new_cursor),
                    },
                    handled_successors=True,
                )
            return NodeResult(success=True, output_data=matches[0])

        async def _stateless_preview(self, token: str) -> NodeResult:
            """Editor `/listen` preview — primes the cursor so the user
            sees one match without persisting state."""
            async with httpx.AsyncClient(timeout=manifest.timeout_seconds) as client:
                # First poll snapshots silently; second primed poll
                # surfaces a match.
                primer = {
                    "event_type": getattr(self.props, "event_type", "") or "",
                    **_scope_dict(manifest, self.props),
                    "known_ids": [],
                    "since": "",
                }
                matches, _ = await _run_poll(self, token, primer, client)
            if not matches:
                return NodeResult(
                    success=True,
                    output_data={
                        "matched": 0,
                        "event_type": getattr(self.props, "event_type", ""),
                    },
                    handled_successors=True,
                )
            return NodeResult(success=True, output_data=matches[0])

    _ManifestTriggerNode.__name__ = f"{manifest.name.replace(' ', '')}TriggerNode"
    _ManifestTriggerNode.__qualname__ = _ManifestTriggerNode.__name__

    # Scheduler binding — registers the same poll path for backend cron.
    async def _poll_for_scheduler(
        token: str,
        cursor: dict[str, Any] | None,
        props: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        node = _ManifestTriggerNode.__new__(_ManifestTriggerNode)
        node.credential = None
        node.props = Props(**props)  # type: ignore[arg-type]
        async with httpx.AsyncClient(timeout=manifest.timeout_seconds) as client:
            return await _run_poll(node, token, cursor, client)

    try:
        from apps.api.app.execution_engine.scheduler.integration_polling import (
            register_poller,
        )

        _token_fields = (
            manifest.token_field
            if isinstance(manifest.token_field, list)
            else [manifest.token_field]
        )
        register_poller(
            node_type=manifest.type,
            provider=manifest.provider,
            poller=_poll_for_scheduler,
            token_fields=_token_fields,
        )
    except Exception:  # noqa: BLE001
        # Scheduler module unavailable (tests that don't import the
        # worker). Skip registration silently — the node still works
        # for direct execute() calls.
        pass

    return _ManifestTriggerNode


__all__ = ["build_polling_trigger"]
