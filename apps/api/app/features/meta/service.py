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

        # WhatsApp resources — both WABA accounts and the registered phone
        # numbers underneath them are exposed. Most nodes care about a
        # specific phone number id (that's what the Send API uses), so
        # `waba_phone` is the default selector.
        wabas = data.get("whatsapp_business_accounts") or []
        if not isinstance(wabas, list):
            wabas = []

        if kind == "waba":
            return [
                MetaResource(
                    id=str(w.get("id") or ""),
                    name=str(w.get("name") or w.get("id") or ""),
                    kind="waba",
                    secondary=w.get("business_name"),
                )
                for w in wabas
                if w.get("id")
            ]

        if kind == "waba_phone":
            out2: list[MetaResource] = []
            for w in wabas:
                phones = (w.get("phone_numbers") or {}).get("data") or []
                for phone in phones:
                    if not isinstance(phone, dict) or not phone.get("id"):
                        continue
                    label = (
                        str(phone.get("verified_name") or "")
                        or str(phone.get("display_phone_number") or "")
                        or str(phone.get("id"))
                    )
                    out2.append(
                        MetaResource(
                            id=str(phone["id"]),
                            name=label,
                            kind="waba_phone",
                            secondary=str(phone.get("display_phone_number") or w.get("name") or ""),
                        )
                    )
            return out2

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
    # Messenger send-message — used by action.meta.fb_send_message.
    # ------------------------------------------------------------------

    async def fb_send_message(
        self,
        page_access_token: str,
        page_id: str,
        recipient_id: str,
        text: str,
        messaging_type: str = "RESPONSE",
        message_tag: str | None = None,
    ) -> dict[str, Any]:
        """Send a Messenger DM via the Send API.

        Args:
          page_access_token: page-level token from the credential's `pages` array.
          page_id:           FB Page id (NOT the recipient's PSID).
          recipient_id:      Page-Scoped User ID (PSID) — from the upstream
                             webhook's `sender.id`.
          text:              message body.
          messaging_type:    'RESPONSE' (within 24h), 'UPDATE' (transactional),
                             or 'MESSAGE_TAG' (when paired with `message_tag`).
          message_tag:       one of HUMAN_AGENT, CONFIRMED_EVENT_UPDATE,
                             POST_PURCHASE_UPDATE, ACCOUNT_UPDATE — only honored
                             when messaging_type == 'MESSAGE_TAG'.

        Meta enforces the 24h window server-side. Calls outside the window
        without an appropriate `message_tag` come back as error 10/2018278;
        we surface those verbatim so the workflow log shows Meta's exact
        rejection reason.
        """
        payload: dict[str, Any] = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
            "messaging_type": messaging_type,
        }
        if messaging_type == "MESSAGE_TAG" and message_tag:
            payload["tag"] = message_tag

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                _graph_url(f"/{page_id}/messages"),
                params={"access_token": page_access_token},
                json=payload,
            )
        body = resp.json()
        if resp.status_code >= 400:
            err = body.get("error", {})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Messenger send failed: {err.get('message') or body}",
            )
        return body

    # ------------------------------------------------------------------
    # Comment replies (IG + FB) and Page post publish — small Graph API
    # wrappers used by the corresponding action nodes.
    # ------------------------------------------------------------------

    async def ig_reply_comment(
        self,
        page_access_token: str,
        comment_id: str,
        message: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                _graph_url(f"/{comment_id}/replies"),
                params={"access_token": page_access_token, "message": message},
            )
        body = resp.json()
        if resp.status_code >= 400:
            err = body.get("error", {})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IG comment reply failed: {err.get('message') or body}",
            )
        return body

    async def fb_reply_comment(
        self,
        page_access_token: str,
        comment_id: str,
        message: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                _graph_url(f"/{comment_id}/comments"),
                params={"access_token": page_access_token},
                json={"message": message},
            )
        body = resp.json()
        if resp.status_code >= 400:
            err = body.get("error", {})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"FB comment reply failed: {err.get('message') or body}",
            )
        return body

    async def fb_publish_post(
        self,
        page_access_token: str,
        page_id: str,
        message: str,
        link: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": message}
        if link:
            payload["link"] = link
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _graph_url(f"/{page_id}/feed"),
                params={"access_token": page_access_token},
                json=payload,
            )
        body = resp.json()
        if resp.status_code >= 400:
            err = body.get("error", {})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"FB post publish failed: {err.get('message') or body}",
            )
        return body

    # ------------------------------------------------------------------
    # IG publish (feed + story) — two-step container API:
    #   1. POST /{ig_user_id}/media   → returns creation_id
    #   2. poll  /{creation_id}        until status_code=FINISHED
    #   3. POST /{ig_user_id}/media_publish with creation_id
    # ------------------------------------------------------------------

    async def ig_publish_media(
        self,
        page_access_token: str,
        ig_user_id: str,
        media_url: str,
        kind: str,  # 'IMAGE' | 'VIDEO' | 'REELS' | 'STORIES'
        caption: str | None = None,
        max_poll_seconds: int = 60,
    ) -> dict[str, Any]:
        """Synchronous IG publish — creates the media container, polls until
        Meta finishes processing it, then publishes. Caller's workflow run
        blocks for `max_poll_seconds` worst case. Suitable for image posts
        and short videos; for large videos / Reels, switch to an async
        worker pattern (PR C scope).
        """
        import asyncio

        kind_upper = kind.upper()
        params: dict[str, Any] = {"access_token": page_access_token}
        # `image_url` for IMAGE; `video_url` + `media_type` for VIDEO / REELS / STORIES.
        if kind_upper == "IMAGE":
            params["image_url"] = media_url
        else:
            params["video_url"] = media_url
            params["media_type"] = kind_upper
        if caption is not None:
            params["caption"] = caption
        if kind_upper == "STORIES":
            # Stories accept either image_url or video_url; remove `caption`
            # since story containers don't take captions.
            params.pop("caption", None)

        async with httpx.AsyncClient(timeout=60.0) as client:
            container_resp = await client.post(
                _graph_url(f"/{ig_user_id}/media"),
                params=params,
            )
            container = container_resp.json()
            if container_resp.status_code >= 400 or "id" not in container:
                err = container.get("error", {})
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"IG media container failed: {err.get('message') or container}",
                )
            creation_id = container["id"]

            # Poll until FINISHED. Image posts usually return FINISHED on
            # the first call; videos take 5-30s. Bail with a clear error
            # if Meta returns ERROR.
            elapsed = 0
            poll_interval = 2
            while elapsed < max_poll_seconds:
                status_resp = await client.get(
                    _graph_url(f"/{creation_id}"),
                    params={
                        "access_token": page_access_token,
                        "fields": "status_code",
                    },
                )
                status_body = status_resp.json()
                code = str(status_body.get("status_code") or "")
                if code == "FINISHED":
                    break
                if code == "ERROR":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"IG media processing failed: {status_body}",
                    )
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
            else:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=(
                        f"IG media processing did not finish within "
                        f"{max_poll_seconds}s. Container id: {creation_id}"
                    ),
                )

            publish_resp = await client.post(
                _graph_url(f"/{ig_user_id}/media_publish"),
                params={
                    "access_token": page_access_token,
                    "creation_id": creation_id,
                },
            )
            publish = publish_resp.json()
            if publish_resp.status_code >= 400:
                err = publish.get("error", {})
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"IG media publish failed: {err.get('message') or publish}",
                )
            return publish

    # ------------------------------------------------------------------
    # WhatsApp Cloud API — text/template sends, mark-as-read, template list.
    #
    # The user picks a `phone_number_id` (kind=waba_phone) per node; that
    # id is what every WA Send API call is keyed on. The access token here
    # is the *user* long-lived token from the OAuth credential — enterprise
    # setups should switch to a permanent System User token (PR 2c-B+).
    # ------------------------------------------------------------------

    async def wa_send_text(
        self,
        access_token: str,
        phone_number_id: str,
        to: str,
        text: str,
        preview_url: bool = False,
        reply_to_message_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a free-form WhatsApp text message.

        Valid only within the 24-hour customer-service window since the
        recipient's last inbound message. Outside that window Meta returns
        error 131047 ("Message failed to send because more than 24 hours
        have passed since the customer last replied to this number"). For
        outside-window sends, use `wa_send_template`.
        """
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"preview_url": preview_url, "body": text},
        }
        if reply_to_message_id:
            payload["context"] = {"message_id": reply_to_message_id}
        return await self._wa_send(access_token, phone_number_id, payload)

    async def wa_mark_read(
        self,
        access_token: str,
        phone_number_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Mark an inbound WhatsApp message as read — surfaces the blue
        double check in the user's app."""
        return await self._wa_send(
            access_token,
            phone_number_id,
            {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
            },
        )

    async def _wa_send(
        self,
        access_token: str,
        phone_number_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                _graph_url(f"/{phone_number_id}/messages"),
                headers={"Authorization": f"Bearer {access_token}"},
                json=payload,
            )
        body = resp.json()
        if resp.status_code >= 400:
            err = body.get("error", {})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"WhatsApp send failed: {err.get('message') or body}",
            )
        return body

    # ------------------------------------------------------------------
    # Lead Ads — fetch the lead details by leadgen_id. The webhook only
    # delivers the id; this hop pulls the full form submission.
    # ------------------------------------------------------------------

    async def lead_fetch(
        self,
        page_access_token: str,
        leadgen_id: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                _graph_url(f"/{leadgen_id}"),
                params={
                    "access_token": page_access_token,
                    "fields": "id,created_time,ad_id,form_id,field_data,partner_name",
                },
            )
        body = resp.json()
        if resp.status_code >= 400:
            err = body.get("error", {})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Lead fetch failed: {err.get('message') or body}. "
                    "Confirm the Page admin granted Lead Access to your app "
                    "in Page Settings."
                ),
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
    """Normalize Meta's two envelope shapes into a uniform list of synthesized
    `{field, value}` rows.

    Meta delivers events under two top-level keys:
      - `entry.changes[]` — content events (FB feed posts, IG comments,
        mentions, reactions, lead_gen). Each row carries a `field` we can
        often use verbatim, though FB `feed` is overloaded and we sub-
        classify based on the row's `item` so a comment doesn't masquerade
        as a status update.
      - `entry.messaging[]` — conversational events (Messenger DMs, IG
        DMs, story replies, story @mentions, postbacks, reactions). The
        outer `field` doesn't exist on these — we synthesize one from the
        message's shape so the routing table can stay flat.

    The synthesized field is stable across rebuilds — never inline the
    raw Meta keys in `_TRIGGER_MAP`; always go through this normalizer.
    """
    out: list[dict[str, Any]] = []

    for change in entry.get("changes") or []:
        raw_field = change.get("field")
        if not raw_field:
            continue
        value = change.get("value") or {}
        field = str(raw_field)

        # FB Page `feed` is overloaded — split by the row's `item`. A
        # `feed/comment` event has a different downstream shape than a
        # `feed/post`, and routing them through one trigger type would
        # force every consumer to redo the disambiguation.
        if field == "feed":
            item = str(value.get("item") or "").lower()
            if item == "comment":
                field = "feed.comment"
            elif item == "post":
                field = "feed.post"
            elif item == "reaction":
                field = "feed.reaction"
            else:
                field = "feed.other"

        # WhatsApp deliveries arrive as `field == "messages"` but the
        # value carries two distinct payloads — inbound messages (a
        # `messages[]` array) and status callbacks (a `statuses[]`
        # array). Fork into one synthesized row per inbound message and
        # one per status so trigger nodes don't have to loop themselves.
        if object_type == "whatsapp_business_account" and field == "messages":
            for m in value.get("messages") or []:
                if isinstance(m, dict):
                    out.append({"field": "wa.messages", "value": {**value, "_event": m}})
            for s in value.get("statuses") or []:
                if isinstance(s, dict):
                    out.append({"field": "wa.statuses", "value": {**value, "_event": s}})
            # Either branch fired (or both empty) — never bubble the raw row.
            continue

        out.append({"field": field, "value": value})

    for msg in entry.get("messaging") or []:
        out.append({"field": _classify_messaging(object_type, msg), "value": msg})

    return out


def _classify_messaging(object_type: str | None, msg: dict[str, Any]) -> str:
    """Synthesize a stable field tag for `messaging[]` rows so the routing
    table can fan out by intent (DM vs story reply vs story mention vs
    postback) without every consumer re-parsing Meta's payload.
    """
    if "postback" in msg:
        return "messaging.postback"
    if "reaction" in msg:
        return "messaging.reaction"

    message = msg.get("message")
    if not isinstance(message, dict):
        return "messaging.unknown"

    # IG story sub-types live inside the `message` body. They only appear
    # on `object: instagram` — Messenger never sends them. We still gate
    # on object_type so a misrouted payload can't accidentally fire an
    # IG story-reply workflow on a Messenger DM.
    if object_type == "instagram":
        attachments = message.get("attachments") or []
        if isinstance(attachments, list):
            for att in attachments:
                if isinstance(att, dict) and str(att.get("type") or "") == "story_mention":
                    return "messaging.ig_story_mention"
        reply_to = message.get("reply_to") or {}
        if isinstance(reply_to, dict) and reply_to.get("story"):
            return "messaging.ig_story_reply"

    return "messaging.text"


# (object, synthesized_field) → Fuse trigger node type. The fields here
# are the ones `_flatten_entry` emits, NOT Meta's raw envelope fields.
# Phase 2 routes every Messenger / IG inbox / Page feed / Lead Ads event
# through this map; Phase 2b will add the `whatsapp_business_account`
# entries. PR B in Phase 2 only adds node modules — the routing is
# already in place here.
_TRIGGER_MAP: dict[tuple[str, str], str] = {
    # Instagram
    ("instagram", "comments"): "trigger.meta.ig_comment",
    ("instagram", "mentions"): "trigger.meta.ig_mention",
    ("instagram", "messaging.text"): "trigger.meta.ig_message",
    ("instagram", "messaging.ig_story_reply"): "trigger.meta.ig_story_reply",
    ("instagram", "messaging.ig_story_mention"): "trigger.meta.ig_story_mention",
    # Facebook Page / Messenger
    ("page", "messaging.text"): "trigger.meta.fb_message",
    ("page", "messaging.postback"): "trigger.meta.fb_postback",
    ("page", "feed.comment"): "trigger.meta.fb_comment",
    ("page", "feed.reaction"): "trigger.meta.fb_reaction",
    ("page", "mention"): "trigger.meta.fb_mention",
    # Lead Ads (delivered under the `page` object)
    ("page", "leadgen"): "trigger.meta.lead_submission",
    # WhatsApp Cloud API — split inside _flatten_entry into one event
    # per inbound message (`wa.messages`) or status callback (`wa.statuses`).
    ("whatsapp_business_account", "wa.messages"): "trigger.meta.wa_message",
    ("whatsapp_business_account", "wa.statuses"): "trigger.meta.wa_status",
}


def _trigger_type_for(object_type: str | None, field: str) -> str | None:
    if not object_type:
        return None
    return _TRIGGER_MAP.get((object_type, field))


# Per-trigger property filter so webhook routing only fires the workflow
# whose trigger node points at the *same* target id Meta delivered the
# event for. Keep these aligned with the trigger node's saved properties
# (the property names below must match the node's Pydantic model fields).
_TARGET_FILTER_BY_TRIGGER: dict[str, str] = {
    # Instagram triggers — target_id is the IG business account id.
    "trigger.meta.ig_comment": "ig_account_id",
    "trigger.meta.ig_mention": "ig_account_id",
    "trigger.meta.ig_message": "ig_account_id",
    "trigger.meta.ig_story_reply": "ig_account_id",
    "trigger.meta.ig_story_mention": "ig_account_id",
    # Page triggers — target_id is the FB Page id.
    "trigger.meta.fb_message": "page_id",
    "trigger.meta.fb_postback": "page_id",
    "trigger.meta.fb_comment": "page_id",
    "trigger.meta.fb_reaction": "page_id",
    "trigger.meta.fb_mention": "page_id",
    # Lead Ads — target_id is the FB Page id; lead-form filtering happens
    # inside the trigger node since Meta only sends `form_id` in the
    # value, not as a separate routing key.
    "trigger.meta.lead_submission": "page_id",
    # WhatsApp — target_id is the WABA id (entry.id in the envelope).
    # Phone-number filtering happens inside the trigger node since one
    # WABA can own multiple numbers and users wire one per node.
    "trigger.meta.wa_message": "waba_id",
    "trigger.meta.wa_status": "waba_id",
}


def _target_filters(trigger_type: str, target_id: str) -> dict[str, str]:
    field = _TARGET_FILTER_BY_TRIGGER.get(trigger_type)
    if not field:
        return {}
    return {field: target_id}


def get_meta_service(db: AsyncSession) -> MetaService:
    return MetaService(db)
