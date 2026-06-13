from __future__ import annotations

import hashlib
import hmac
import json
import uuid as _uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.logger import get_logger
from apps.api.app.features.credentials.service import CredentialService
from apps.api.app.features.meta.schemas import MetaResource, WATemplate

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

    async def wa_send_template(
        self,
        access_token: str,
        phone_number_id: str,
        to: str,
        template_name: str,
        language_code: str,
        body_variables: list[str] | None = None,
    ) -> dict[str, Any]:
        """Send a pre-approved WhatsApp template message.

        Templates are the only way to reach a user OUTSIDE the 24-hour
        customer-service window. Each template lives in the WABA's
        message_templates list and must be APPROVED by Meta before it
        can be sent — submitted templates are reviewed in ~24-48 hours.

        Args:
          template_name:  exact template name as registered in the WABA.
          language_code:  e.g. "en_US", "es", "pt_BR".
          body_variables: positional values substituted into the template's
                          `{{1}}`, `{{2}}`, ... body placeholders. Header and
                          button parameters are not exposed by this helper —
                          they need their own component entries, which we'll
                          add once the simpler body-only path is proven.
        """
        components: list[dict[str, Any]] = []
        if body_variables:
            components.append(
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(v)} for v in body_variables],
                }
            )

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components,
            },
        }
        return await self._wa_send(access_token, phone_number_id, payload)

    # ------------------------------------------------------------------
    # Template list — powers the `wa-template` field type in the editor.
    # The Graph API returns a richer payload; this projection extracts
    # just the (id, name, language, status, body) the picker needs.
    # ------------------------------------------------------------------

    async def wa_list_templates(
        self,
        access_token: str,
        waba_id: str,
        limit: int = 100,
    ) -> list[WATemplate]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                _graph_url(f"/{waba_id}/message_templates"),
                headers={"Authorization": f"Bearer {access_token}"},
                params={"limit": limit},
            )
        body = resp.json()
        if resp.status_code >= 400:
            err = body.get("error", {})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"WhatsApp template list failed: {err.get('message') or body}. "
                    "Confirm the credential has whatsapp_business_management scope "
                    "and the WABA is reachable through this account."
                ),
            )

        templates: list[WATemplate] = []
        for tpl in body.get("data") or []:
            if not isinstance(tpl, dict):
                continue
            body_preview = ""
            var_count = 0
            for comp in tpl.get("components") or []:
                if not isinstance(comp, dict):
                    continue
                if str(comp.get("type") or "").upper() != "BODY":
                    continue
                text = str(comp.get("text") or "")
                body_preview = text
                # Count `{{N}}` placeholders — Meta numbers them positionally
                # starting at 1 and surfaces a `body_text_named_params` array
                # only on newer named-parameter templates. The positional
                # count is the source of truth for the legacy components API
                # we use in wa_send_template.
                import re

                var_count = len(set(re.findall(r"\{\{(\d+)\}\}", text)))
                break
            templates.append(
                WATemplate(
                    id=str(tpl.get("id") or tpl.get("name") or ""),
                    name=str(tpl.get("name") or ""),
                    language=str(tpl.get("language") or ""),
                    status=str(tpl.get("status") or "UNKNOWN"),
                    category=tpl.get("category"),
                    body_variable_count=var_count,
                    body_preview=body_preview,
                    raw=tpl,
                )
            )
        return templates

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
        from apps.api.app.features.meta.repository import MetaSubscriptionRepository
        from apps.api.app.features.workflows.repository import WorkflowRepository
        from apps.api.app.node_system.execution.execution_engine import execution_engine

        sub_repo = MetaSubscriptionRepository(self.db)
        wf_repo = WorkflowRepository(self.db)
        execution_ids: list[str] = []
        triggered = 0

        for entry in entries:
            target_id = str(entry.get("id") or "")
            # Two envelope shapes: `changes` (FB Page, IG, WhatsApp) and
            # `messaging` (Messenger, IG DMs, IG story reply / mention).
            # Both normalize through `_flatten_entry` into uniform events.
            events = _flatten_entry(object_type, entry)
            for event in events:
                if not object_type:
                    continue
                # DB-indexed routing — composite index on
                # (object_type, target_id, field) makes this O(log N).
                # Replaces the Phase 1/2 graph scan via
                # `WorkflowRepository.find_by_trigger_type`.
                subs = await sub_repo.lookup(object_type, target_id, event["field"])
                if not subs:
                    continue

                # Group by workflow_id so each workflow fires at most once
                # per envelope event, even if it owns multiple trigger
                # nodes pointing at the same target.
                seen_workflows: set[Any] = set()
                for sub in subs:
                    if sub.workflow_id in seen_workflows:
                        continue
                    seen_workflows.add(sub.workflow_id)
                    wf = await wf_repo.get_by_id(sub.workflow_id)
                    if wf is None or not wf.is_active:
                        continue

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
                            trigger_type=sub.trigger_type,
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


# ──────────────────────────────────────────────────────────────────────────
# Workflow ↔ MetaSubscription sync
#
# Public hooks called from the workflow lifecycle (see WorkflowService):
#   sync_workflow_subscriptions(db, workflow) → after every save
#   cleanup_workflow_subscriptions(db, workflow_id) → before delete
#
# These live as module-level functions (not MetaService methods) so the
# workflow service can call them without importing MetaService's full
# surface area, keeping the dependency direction one-way.
# ──────────────────────────────────────────────────────────────────────────


# Per-trigger description of how to extract the routing tuple from a
# workflow node's saved properties. Keeps `sync_workflow_subscriptions`
# generic — adding a new Meta trigger is one entry here, not a new branch.
_TRIGGER_SPECS: dict[str, dict[str, str]] = {
    # Instagram
    "trigger.meta.ig_comment": {
        "object_type": "instagram",
        "field": "comments",
        "target_prop": "ig_account_id",
    },
    "trigger.meta.ig_mention": {
        "object_type": "instagram",
        "field": "mentions",
        "target_prop": "ig_account_id",
    },
    "trigger.meta.ig_message": {
        "object_type": "instagram",
        "field": "messaging.text",
        "target_prop": "ig_account_id",
    },
    "trigger.meta.ig_story_reply": {
        "object_type": "instagram",
        "field": "messaging.ig_story_reply",
        "target_prop": "ig_account_id",
    },
    "trigger.meta.ig_story_mention": {
        "object_type": "instagram",
        "field": "messaging.ig_story_mention",
        "target_prop": "ig_account_id",
    },
    # Facebook Page / Messenger
    "trigger.meta.fb_message": {
        "object_type": "page",
        "field": "messaging.text",
        "target_prop": "page_id",
    },
    "trigger.meta.fb_postback": {
        "object_type": "page",
        "field": "messaging.postback",
        "target_prop": "page_id",
    },
    "trigger.meta.fb_comment": {
        "object_type": "page",
        "field": "feed.comment",
        "target_prop": "page_id",
    },
    "trigger.meta.fb_reaction": {
        "object_type": "page",
        "field": "feed.reaction",
        "target_prop": "page_id",
    },
    "trigger.meta.fb_mention": {
        "object_type": "page",
        "field": "mention",
        "target_prop": "page_id",
    },
    # Lead Ads (delivered on the page object)
    "trigger.meta.lead_submission": {
        "object_type": "page",
        "field": "leadgen",
        "target_prop": "page_id",
    },
    # WhatsApp
    "trigger.meta.wa_message": {
        "object_type": "whatsapp_business_account",
        "field": "wa.messages",
        "target_prop": "waba_id",
    },
    "trigger.meta.wa_status": {
        "object_type": "whatsapp_business_account",
        "field": "wa.statuses",
        "target_prop": "waba_id",
    },
}


# Self-check: every entry in `_TRIGGER_SPECS` must round-trip through
# `_TRIGGER_MAP` so the sync layer and the webhook router can't drift.
# Triggered at import — if someone edits one map without the other,
# pytest collection fails immediately rather than at first webhook.
for _trigger_type, _spec in _TRIGGER_SPECS.items():
    _expected = _TRIGGER_MAP.get((_spec["object_type"], _spec["field"]))
    if _expected != _trigger_type:
        raise RuntimeError(
            f"_TRIGGER_SPECS / _TRIGGER_MAP drift: {_trigger_type} → "
            f"({_spec['object_type']}, {_spec['field']}) but _TRIGGER_MAP "
            f"resolves to {_expected!r}"
        )


def _scan_meta_triggers(workflow: Any) -> list[dict[str, Any]]:
    """Pull every `trigger.meta.*` node out of a workflow graph alongside
    its saved properties + the routing spec we'll use to build a row."""
    graph = getattr(workflow, "graph", None) or {}
    nodes = graph.get("nodes") or []
    out: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("type") or "")
        spec = _TRIGGER_SPECS.get(node_type)
        if not spec:
            continue
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        props = (node.get("data") or {}).get("properties") or {}
        target_id = str(props.get(spec["target_prop"]) or "").strip()
        credential_id = str(props.get("credential") or "").strip()
        out.append(
            {
                "node_id": node_id,
                "trigger_type": node_type,
                "object_type": spec["object_type"],
                "field": spec["field"],
                "target_id": target_id,
                "credential_id": credential_id,
            }
        )
    return out


async def sync_workflow_subscriptions(db: AsyncSession, workflow: Any) -> None:
    """Reconcile MetaSubscription rows against the workflow's current graph.

    Called from `WorkflowService.update_workflow` and `create_workflow`
    after each save. The routing table updates atomically with the user's
    edit so the very next webhook delivery hits the right row — no lag
    from a background reconciler.

    Meta-side subscribed_apps registration runs best-effort inside the
    same call; if Meta returns an error (e.g. revoked permissions) the
    row is still written so routing works for any user who manually
    re-subscribes the target in the Meta dashboard. The error message
    is captured on `last_error` so the editor can surface a banner later.
    """
    import uuid as _uuid

    from apps.api.app.features.meta.models import MetaSubscription
    from apps.api.app.features.meta.repository import MetaSubscriptionRepository

    repo = MetaSubscriptionRepository(db)
    triggers = _scan_meta_triggers(workflow)
    keep_node_ids: set[str] = set()

    for entry in triggers:
        # Skip incomplete configurations — the trigger node carries
        # required fields, but during in-progress editing the user might
        # save with no target_id / credential. Don't materialize a useless
        # row; it'll come back once the user finishes wiring it up.
        if not entry["target_id"] or not entry["credential_id"]:
            continue
        try:
            credential_uuid = _uuid.UUID(entry["credential_id"])
        except (ValueError, TypeError):
            continue

        keep_node_ids.add(entry["node_id"])
        sub = MetaSubscription(
            user_id=workflow.user_id,
            workspace_id=workflow.workspace_id,
            credential_id=credential_uuid,
            workflow_id=workflow.id,
            node_id=entry["node_id"],
            trigger_type=entry["trigger_type"],
            object_type=entry["object_type"],
            target_id=entry["target_id"],
            field=entry["field"],
            is_active=bool(getattr(workflow, "is_active", True)),
        )
        upserted = await repo.upsert(sub)

        # Meta-side registration only fires if we haven't successfully
        # subscribed this target before, or the target id changed (upsert
        # resets `meta_subscribed_at`). Skip the API hop on every save
        # otherwise — Meta rate-limits these.
        if upserted.meta_subscribed_at is None:
            try:
                await _meta_subscribe_target(db, upserted)
                upserted.meta_subscribed_at = datetime.now(UTC)
                upserted.last_error = None
            except Exception as exc:  # noqa: BLE001 — surface but don't fail save
                logger.exception(
                    f"Meta subscribe failed for workflow={workflow.id} node={entry['node_id']}: {exc}"
                )
                upserted.last_error = str(exc)[:1024]

    # Drop rows for nodes that are no longer in the graph (deleted or
    # retyped). We don't unsubscribe from Meta's side here — other
    # workflows on the same credential may still need the target.
    await repo.delete_missing_nodes(workflow.id, keep_node_ids)


async def cleanup_workflow_subscriptions(db: AsyncSession, workflow_id: Any) -> None:
    """Drop every MetaSubscription row for the deleted workflow.

    Like `sync_workflow_subscriptions`, we leave Meta-side subscriptions
    alone — sharing a Page with another workflow under the same
    credential is the common case, and tearing down would orphan it.
    """
    from apps.api.app.features.meta.repository import MetaSubscriptionRepository

    repo = MetaSubscriptionRepository(db)
    await repo.delete_for_workflow(workflow_id)


async def _meta_subscribe_target(db: AsyncSession, sub: Any) -> None:
    """Register Meta's webhook delivery for the target referenced by `sub`.

    For Page / Instagram (linked through a Page) we hit
    `POST /{page_id}/subscribed_apps` with the page access token. For
    WhatsApp we hit `POST /{waba_id}/subscribed_apps` with the user
    long-lived token. Failures bubble up — `sync_workflow_subscriptions`
    captures them onto `last_error`.
    """
    from apps.api.app.features.credentials.service import CredentialService

    cred_service = CredentialService(db)
    credential = await cred_service.repo.get_by_id_and_workspace(
        sub.credential_id, sub.workspace_id
    )
    if credential is None:
        raise ValueError("Meta credential not found")
    data = await cred_service.get_decrypted_credential(credential)

    if sub.object_type == "whatsapp_business_account":
        access_token = str((data or {}).get("access_token") or "")
        if not access_token:
            raise ValueError("Meta credential missing access_token for WhatsApp subscribe")
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                _graph_url(f"/{sub.target_id}/subscribed_apps"),
                headers={"Authorization": f"Bearer {access_token}"},
            )
        body = resp.json()
        if resp.status_code >= 400 or not body.get("success", True):
            err = body.get("error", {})
            raise ValueError(f"WhatsApp subscribe_apps failed: {err.get('message') or body}")
        return

    # Page / Instagram. IG events flow through the linked Page's
    # subscribed_apps registration — the Meta dashboard's per-object
    # subscription is global; per-Page activation is what this call does.
    pages = (data or {}).get("pages") or []
    page_token: str | None = None
    if sub.object_type == "page":
        for p in pages:
            if isinstance(p, dict) and str(p.get("id") or "") == sub.target_id:
                token = p.get("access_token")
                if isinstance(token, str) and token:
                    page_token = token
                page_target_id = sub.target_id
                break
    else:  # instagram — find the Page that owns this IG business account
        page_target_id = None
        for p in pages:
            if not isinstance(p, dict):
                continue
            ig = p.get("instagram_business_account") or {}
            if str(ig.get("id") or "") == sub.target_id:
                token = p.get("access_token")
                if isinstance(token, str) and token:
                    page_token = token
                page_target_id = str(p.get("id") or "")
                break
        if not page_target_id:
            raise ValueError("No Page linked to this Instagram account")

    if not page_token:
        raise ValueError("No page access token for this target")

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            _graph_url(f"/{page_target_id}/subscribed_apps"),
            params={"access_token": page_token},
        )
    body = resp.json()
    if resp.status_code >= 400 or not body.get("success", True):
        err = body.get("error", {})
        raise ValueError(f"subscribed_apps failed: {err.get('message') or body}")
