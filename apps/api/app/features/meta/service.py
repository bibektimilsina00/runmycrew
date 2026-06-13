from __future__ import annotations

import hashlib
import hmac
import json
import uuid as _uuid
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.logger import get_logger
from apps.api.app.features.credentials.service import CredentialService
from apps.api.app.features.meta.schemas import MetaResource

logger = get_logger(__name__)


def _graph_url(path: str) -> str:
    return f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}{path}"


def verify_webhook_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Verify Meta's `X-Hub-Signature-256` header against the app secret.

    Meta signs the raw payload bytes (NOT the JSON-decoded version) with
    HMAC-SHA256, formatted as `sha256=<hex>`. Returns False on missing
    header, missing app secret, or any mismatch — never raises.
    """
    if not signature_header or not settings.META_APP_SECRET:
        return False
    try:
        scheme, sig = signature_header.split("=", 1)
    except ValueError:
        return False
    if scheme.lower() != "sha256":
        return False
    expected = hmac.new(
        settings.META_APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig)


class MetaService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Resource discovery (powering the `meta-resource` field type)
    # ------------------------------------------------------------------

    async def list_resources(
        self,
        credential_id: _uuid.UUID,
        kind: str,
        user: Any,
        workspace: Any,
    ) -> list[MetaResource]:
        """Return the resources of `kind` reachable through `credential_id`.

        Phase 1 supports `page` and `ig_account`. WhatsApp + Lead Ads
        forms come in subsequent phases.
        """
        cred_service = CredentialService(self.db)
        data = await cred_service.get_decrypted(credential_id, user, workspace)

        # Pages are already enriched in the OAuth callback (see
        # MetaOAuthProvider.exchange_code), so resource lookup is a cheap
        # in-memory read instead of an extra Graph API hop.
        pages = data.get("pages") or []
        if not isinstance(pages, list):
            pages = []

        if kind == "page":
            return [
                MetaResource(
                    id=str(p.get("id")),
                    name=str(p.get("name") or p.get("id")),
                    kind="page",
                    secondary=p.get("category"),
                )
                for p in pages
                if p.get("id")
            ]

        if kind == "ig_account":
            out: list[MetaResource] = []
            for p in pages:
                ig = p.get("instagram_business_account") or {}
                ig_id = ig.get("id")
                if not ig_id:
                    continue
                out.append(
                    MetaResource(
                        id=str(ig_id),
                        name=str(ig.get("username") or ig_id),
                        kind="ig_account",
                        secondary=p.get("name"),
                    )
                )
            return out

        # waba_phone + lead_form land in later phases.
        return []

    # ------------------------------------------------------------------
    # IG send-DM — used by action.meta.ig_send_dm and re-exposed here so
    # tests / other features can call it without going through the node
    # execution path.
    # ------------------------------------------------------------------

    async def ig_send_dm(
        self,
        page_access_token: str,
        ig_user_id: str,
        recipient_id: str,
        text: str,
    ) -> dict[str, Any]:
        """Send an Instagram DM via the Graph API.

        - `ig_user_id` is the IG *business* account id (NOT the FB Page id).
        - `recipient_id` is the IGSID of the user who interacted (from the
          webhook payload).
        - `page_access_token` is the page-level token derived from the user
          token; stored under `data.pages[].access_token`.
        - Meta enforces a 24-hour messaging window from the last user
          interaction. Outside that window the API returns error 10/2018278
          and we surface it to the caller unchanged.
        """
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                _graph_url(f"/{ig_user_id}/messages"),
                params={"access_token": page_access_token},
                json={
                    "recipient": {"id": recipient_id},
                    "message": {"text": text},
                    "messaging_type": "RESPONSE",
                },
            )
        body = resp.json()
        if resp.status_code >= 400:
            err = body.get("error", {})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Instagram send-DM failed: {err.get('message') or body}",
            )
        return body

    # ------------------------------------------------------------------
    # Webhook receive — verifies signature, parses Meta's envelope, and
    # dispatches matching trigger nodes onto the execution engine.
    # ------------------------------------------------------------------

    async def receive_webhook(
        self,
        app_id: str,
        raw_body: bytes,
        signature: str | None,
    ) -> tuple[int, list[str]]:
        # Only accept events for the configured app. The path param exists so
        # future tenancy / per-app routing has a place to grow.
        if settings.META_APP_ID and app_id != settings.META_APP_ID:
            raise HTTPException(status_code=404, detail="Unknown Meta app id")

        if not verify_webhook_signature(raw_body, signature):
            raise HTTPException(status_code=401, detail="Invalid X-Hub-Signature-256")

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            logger.warning(f"Meta webhook: malformed JSON ({exc})")
            raise HTTPException(status_code=400, detail="Malformed JSON") from exc

        object_type = payload.get("object")
        entries = payload.get("entry") or []
        if not isinstance(entries, list):
            return 0, []

        # Lazy-import to dodge circular: triggers → workflows → executions.
        from apps.api.app.features.workflows.repository import WorkflowRepository
        from apps.api.app.node_system.execution.execution_engine import execution_engine

        wf_repo = WorkflowRepository(self.db)
        execution_ids: list[str] = []
        triggered = 0

        for entry in entries:
            target_id = str(entry.get("id") or "")
            # Two envelope shapes: `changes` (FB Page, IG) and `messaging`
            # (Messenger, WA, IG DMs). Normalize both into trigger events.
            events = _flatten_entry(object_type, entry)
            for event in events:
                trigger_type = _trigger_type_for(object_type, event["field"])
                if not trigger_type:
                    continue
                # Find workflows whose graph carries this trigger node bound
                # to this target_id. Property filter keeps us from triggering
                # a workflow on the wrong account's events.
                wfs = await wf_repo.find_by_trigger_type(
                    trigger_type,
                    property_filters=_target_filters(trigger_type, target_id),
                )
                for wf in wfs:
                    trigger_payload = {
                        "object": object_type,
                        "field": event["field"],
                        "target_id": target_id,
                        "value": event["value"],
                        "received_at": entry.get("time"),
                    }
                    try:
                        execution_id = await execution_engine.trigger_workflow(
                            workflow_id=wf.id,
                            graph=wf.graph,
                            trigger_type=trigger_type,
                            input_data=trigger_payload,
                        )
                        execution_ids.append(str(execution_id))
                        triggered += 1
                    except Exception as exc:  # noqa: BLE001 — keep loop alive
                        logger.exception(f"Meta webhook: failed to trigger {wf.id} ({exc})")

        logger.info(
            f"Meta webhook ({object_type}): {triggered} workflow(s) triggered, "
            f"{len(entries)} entries"
        )
        return triggered, execution_ids


def _flatten_entry(object_type: str | None, entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize Meta's two envelope shapes into a uniform list of events.

    Returns a list of `{field, value}` rows. For `changes` (FB feed, IG
    comments, lead_gen) the field is the change-field. For `messaging`
    (Messenger / IG DM / WA inbox) the field is synthesized from the
    object type.
    """
    out: list[dict[str, Any]] = []

    for change in entry.get("changes") or []:
        field = change.get("field")
        if not field:
            continue
        out.append({"field": str(field), "value": change.get("value") or {}})

    for msg in entry.get("messaging") or []:
        # Sub-classify so trigger.meta.ig_message vs ig_story_reply etc.
        # can be dispatched without re-parsing later.
        if "message" in msg:
            field = "messages"
        elif "postback" in msg:
            field = "messaging_postbacks"
        elif "reaction" in msg:
            field = "message_reactions"
        else:
            field = "messages"
        out.append({"field": field, "value": msg})

    return out


# Mapping from (object, field) → Fuse trigger node type. Only Phase 1
# entries are populated — Phase 2+ adds Messenger, WhatsApp, Lead Ads,
# story replies, etc.
_TRIGGER_MAP: dict[tuple[str, str], str] = {
    ("instagram", "comments"): "trigger.meta.ig_comment",
}


def _trigger_type_for(object_type: str | None, field: str) -> str | None:
    if not object_type:
        return None
    return _TRIGGER_MAP.get((object_type, field))


def _target_filters(trigger_type: str, target_id: str) -> dict[str, str]:
    """Per-trigger property filter to constrain webhook routing to the
    workflow whose trigger node references this specific target."""
    if trigger_type == "trigger.meta.ig_comment":
        return {"ig_account_id": target_id}
    return {}


def get_meta_service(db: AsyncSession) -> MetaService:
    return MetaService(db)
