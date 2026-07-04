"""Webhook receiver service — provider-agnostic.

One endpoint serves every manifest-built webhook trigger:
`POST /webhooks/{provider}/{workflow_id}/{node_id}`. Behavior:

  1. Look up the `WebhookTriggerManifest` by `provider`. 404 if unknown.
  2. Load the workflow, find the trigger node by id, pull its props
     (secret, event filter, …). 404 if missing.
  3. Read the signature header named by the manifest and verify against
     the trigger node's secret using the scheme the manifest declares.
     401 if anything fails.
  4. Apply the manifest's event filter to the provider's
     `event_header` — drop deliveries that don't match the node's
     selector.
  5. Project the payload through the manifest's optional `payload_shape`
     and hand to `execution_engine.trigger_workflow`.

Nothing in here is provider-specific. Adding a new webhook integration
is "register a manifest" — no router edits, no service edits.
"""

from __future__ import annotations

import json
import uuid as _uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.logger import get_logger
from apps.api.app.execution_engine.engine import execution_engine
from apps.api.app.features.webhooks.signature_schemes import get_verifier
from apps.api.app.features.workflows.repository import WorkflowRepository
from apps.api.app.node_system.scaffolds.webhook_manifest import (
    EVENT_ANY,
    get_webhook_manifest,
)

logger = get_logger(__name__)


def _default_shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    """Generic payload projection — works for GitHub-shaped deliveries
    (repository / sender / action keys at the top level) and degrades
    gracefully for providers that don't carry those fields. Manifests
    that need more structure ship their own `payload_shape`.
    """
    body: Any = payload
    repository = None
    sender = None
    action = None
    if isinstance(payload, dict):
        repository = (
            (payload.get("repository") or {}).get("full_name")
            if isinstance(payload.get("repository"), dict)
            else payload.get("repository")
        )
        sender = (
            (payload.get("sender") or {}).get("login")
            if isinstance(payload.get("sender"), dict)
            else payload.get("sender")
        )
        action = payload.get("action") if isinstance(payload.get("action"), str) else None
    return {
        "event": event_type,
        "delivery": delivery_id,
        "action": action,
        "repository": repository,
        "sender": sender,
        "body": body,
    }


class WebhookService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def dispatch(
        self,
        *,
        provider: str,
        workflow_id: str,
        node_id: str,
        raw_body: bytes,
        headers: dict[str, str],
        url: str | None = None,
    ) -> dict[str, Any]:
        manifest = get_webhook_manifest(provider)
        if manifest is None:
            raise HTTPException(status_code=404, detail=f"Unknown webhook provider: {provider}")

        try:
            wf_uuid = _uuid.UUID(str(workflow_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid workflow_id") from None

        wf_repo = WorkflowRepository(self.db)
        workflow = await wf_repo.get_by_id(wf_uuid)
        if workflow is None:
            raise HTTPException(status_code=404, detail="Workflow not found")

        node_props = _find_trigger_node_props(workflow, manifest.type, node_id)
        if node_props is None:
            raise HTTPException(
                status_code=404,
                detail=f"No {manifest.type} node with id {node_id!r} on this workflow",
            )

        # ── signature verify ────────────────────────────────────────
        secret = str(node_props.get(manifest.signature.secret_field) or "")
        if manifest.require_secret and not secret:
            raise HTTPException(
                status_code=401, detail="Webhook secret not configured on this trigger node"
            )
        sig_header = _lookup_header(headers, manifest.signature.header_name)
        verifier = get_verifier(manifest.signature.scheme)
        if verifier is None:
            raise HTTPException(
                status_code=500,
                detail=f"Unknown signature scheme {manifest.signature.scheme!r}",
            )
        if manifest.require_secret:
            if not sig_header:
                raise HTTPException(
                    status_code=401, detail=f"Missing {manifest.signature.header_name} header"
                )
            if not verifier(
                raw_body,
                secret,
                sig_header,
                prefix=manifest.signature.prefix,
                headers=headers,
                url=url,
            ):
                raise HTTPException(status_code=401, detail="Invalid signature")

        # ── parse body first — some providers put event kind in body,
        # not a header, so we need the parsed body to resolve event_type.
        try:
            payload = json.loads(raw_body)
        except Exception:
            payload = {"raw": raw_body.decode("utf-8", errors="replace")}

        # ── event filter ────────────────────────────────────────────
        event_type = _lookup_header(headers, manifest.event_header)
        if not event_type and manifest.event_body_path and isinstance(payload, dict):
            event_type = _extract_body_path(payload, manifest.event_body_path) or ""
        event_type = event_type or "unknown"
        delivery_id = (
            _lookup_header(headers, "X-Hub-Delivery")
            or _lookup_header(headers, f"X-{provider.title()}-Delivery")
            or ""
        )

        wanted = str(node_props.get("event") or EVENT_ANY)
        if wanted and wanted != EVENT_ANY and wanted != event_type:
            logger.info(
                "Webhook %s/%s dropped by event filter (wanted=%s, got=%s)",
                provider,
                workflow.id,
                wanted,
                event_type,
            )
            return {"status": "ignored", "event": event_type}

        shape_fn = manifest.payload_shape or _default_shape
        trigger_data = shape_fn(payload, event_type, delivery_id)

        execution_id = await execution_engine.trigger_workflow(
            workflow_id=workflow.id,
            graph=workflow.graph,
            trigger_type=manifest.type,
            input_data=trigger_data,
        )
        logger.info(
            "Webhook %s[%s] -> workflow %s execution %s",
            provider,
            event_type,
            workflow.id,
            execution_id,
        )
        return {
            "status": "accepted",
            "event": event_type,
            "execution_id": str(execution_id),
        }


# ── helpers ─────────────────────────────────────────────────────────


def _find_trigger_node_props(workflow: Any, node_type: str, node_id: str) -> dict[str, Any] | None:
    """Locate `node_id` on the workflow graph and return its data.properties.

    The receiver matches on both type and id so a workflow can carry
    multiple webhook triggers from different providers without a
    misroute when one provider's secret accidentally validates against
    another's payload."""
    graph = getattr(workflow, "graph", {}) or {}
    for node in graph.get("nodes", []) or []:
        if not isinstance(node, dict):
            continue
        if node.get("type") != node_type:
            continue
        if str(node.get("id") or "") != str(node_id):
            continue
        data = node.get("data") or {}
        props = data.get("properties") or {}
        return props if isinstance(props, dict) else {}
    return None


def _extract_body_path(payload: dict[str, Any], path: str) -> str:
    """Walk a dotted key path into a parsed JSON body. Simple path only —
    no array indexing. Returns "" on any miss.

    Used by manifests that put the event kind in the body rather than a
    header (Instantly's `event_type`, Emailbison's `event`, Lemlist's
    `type`). Kept simple by design: if a provider gets fancy with
    nested arrays, they can write a payload_shape and skip the built-in
    routing entirely.
    """
    cur: Any = payload
    for part in path.split("."):
        if not isinstance(cur, dict):
            return ""
        cur = cur.get(part)
    return str(cur) if cur is not None and not isinstance(cur, dict | list) else ""


def _lookup_header(headers: dict[str, str], name: str) -> str:
    """Case-insensitive header lookup.

    FastAPI gives us a plain dict (lowercased on most ASGI stacks but
    not all), so we sweep keys ourselves. Returns '' on miss to keep
    downstream code from sprinkling None checks.
    """
    if not name:
        return ""
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return str(value)
    return ""
