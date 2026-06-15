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


def verify_webhook_signature(
    raw_body: bytes, signature_header: str | None, app_id: str | None = None
) -> bool:
    """Verify Meta's `X-Hub-Signature-256` header against the app secret.

    Meta signs the raw payload bytes (NOT the JSON-decoded version) with
    HMAC-SHA256, formatted as `sha256=<hex>`. We try both configured app
    secrets (Facebook app + Instagram standalone) so deployments that use
    either or both surfaces work without extra wiring. Returns False on
    missing header, no configured secret, or any mismatch — never raises.
    """
    if not signature_header:
        return False
    try:
        scheme, sig = signature_header.split("=", 1)
    except ValueError:
        return False
    if scheme.lower() != "sha256":
        return False

    candidates: list[str] = []
    if app_id and settings.META_INSTAGRAM_APP_ID and app_id == settings.META_INSTAGRAM_APP_ID:
        if settings.META_INSTAGRAM_APP_SECRET:
            candidates.append(settings.META_INSTAGRAM_APP_SECRET)
    elif app_id and settings.META_APP_ID and app_id == settings.META_APP_ID:
        if settings.META_APP_SECRET:
            candidates.append(settings.META_APP_SECRET)
    else:
        # Unknown / unspecified app — fall back to trying every secret we
        # have configured so the call site doesn't have to know the routing.
        if settings.META_APP_SECRET:
            candidates.append(settings.META_APP_SECRET)
        if settings.META_INSTAGRAM_APP_SECRET:
            candidates.append(settings.META_INSTAGRAM_APP_SECRET)
    if not candidates:
        return False

    for secret in candidates:
        expected = hmac.new(
            secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(expected, sig):
            return True
    return False


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

        Supports both credential types:
          - `meta_oauth` (FB Login for Business): pages, ig_account via
            Page link, WABA + waba_phone via business portfolios.
          - `instagram_oauth` (standalone Instagram Login): only
            `ig_account` — the single IG user the credential was issued
            for. `page` / `waba` kinds return [].
        """
        cred_service = CredentialService(self.db)
        cred = await cred_service.repo.get_by_id_and_workspace(credential_id, workspace.id)
        if cred is None:
            return []
        data = await cred_service.get_decrypted_credential(cred)
        cred_type = cred.type or ""

        # Standalone Instagram Login credentials only expose IG accounts.
        if cred_type == "instagram_oauth":
            if kind != "ig_account":
                return []
            ig_accounts = data.get("ig_accounts") or []
            if not isinstance(ig_accounts, list):
                return []
            out_ig: list[MetaResource] = []
            for acc in ig_accounts:
                if not isinstance(acc, dict):
                    continue
                acc_id = acc.get("id")
                if not acc_id:
                    continue
                out_ig.append(
                    MetaResource(
                        id=str(acc_id),
                        name=str(acc.get("username") or acc_id),
                        kind="ig_account",
                        secondary=acc.get("account_type"),
                    )
                )
            return out_ig

        # meta_oauth — pages enriched in OAuth callback (see
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
        graph_base: str | None = None,
    ) -> dict[str, Any]:
        """Send an Instagram DM via the Graph API.

        - `ig_user_id` is the IG *business* account id (NOT the FB Page id).
        - `recipient_id` is the IGSID of the user who interacted (from the
          webhook payload).
        - `page_access_token` is either the FB-Page-level token
          (meta_oauth path) or the IG user token (instagram_oauth path).
        - `graph_base` overrides the default `graph.facebook.com` base.
          Standalone Instagram Login credentials must pass
          `https://graph.instagram.com/<version>`.
        - Meta enforces a 24-hour messaging window from the last user
          interaction. Outside that window the API returns error 10/2018278
          and we surface it to the caller unchanged.
        """
        base = graph_base or f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{base}/{ig_user_id}/messages",
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
        graph_base: str | None = None,
    ) -> dict[str, Any]:
        base = graph_base or f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{base}/{comment_id}/replies",
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

    async def register_messenger_get_started(
        self,
        page_access_token: str,
        page_id: str,
        payload: str = "GET_STARTED_FUSE",
    ) -> dict[str, Any]:
        """Install a Messenger Get Started button on the Page.

        Required (per Meta) for any new conversation to fire a postback
        webhook — without the button, tapping a Messenger thread for the
        first time doesn't dispatch anything Fuse can route. Idempotent
        on Meta's side: re-POSTing the same payload is a no-op.

        Called automatically from the `/listen` and activation paths
        when the workflow contains a `messaging.postback` trigger, so end
        users never have to run a manual API call to make postbacks work.
        """
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                _graph_url(f"/{page_id}/messenger_profile"),
                params={"access_token": page_access_token},
                json={"get_started": {"payload": payload}},
            )
        body = resp.json()
        if resp.status_code >= 400 or body.get("error"):
            err = body.get("error", {}) or {}
            logger.error(
                "Messenger get_started setup failed status=%s page=%s body=%s",
                resp.status_code,
                page_id,
                body,
            )
            parts = [err.get("message") or "unknown error"]
            if err.get("code") is not None:
                parts.append(f"code={err.get('code')}")
            if err.get("error_subcode") is not None:
                parts.append(f"subcode={err.get('error_subcode')}")
            if err.get("fbtrace_id"):
                parts.append(f"trace={err.get('fbtrace_id')}")
            raise ValueError("Messenger get_started setup failed: " + " | ".join(parts))
        return body

    async def fb_publish_post(
        self,
        page_access_token: str,
        page_id: str,
        message: str,
        link: str | None = None,
        media_url: str | None = None,
        media_kind: str = "IMAGE",
    ) -> dict[str, Any]:
        """Publish to a Facebook Page.

        Routes to one of three endpoints based on what the caller passed:

          - `media_url` + kind=IMAGE → POST `/{page_id}/photos`
            (image post — `message` becomes the caption)
          - `media_url` + kind=VIDEO → POST `/{page_id}/videos`
            (video post — `message` becomes the description)
          - text-only → POST `/{page_id}/feed`
            (status update + optional link preview)

        `link` is ignored on media routes because the Page UI already
        renders the media as the post's primary content; a link card on
        top of an image looks broken to viewers.
        """
        kind_upper = (media_kind or "IMAGE").upper()
        if media_url:
            if kind_upper == "IMAGE":
                endpoint = f"/{page_id}/photos"
                payload: dict[str, Any] = {"url": media_url}
                if message:
                    payload["caption"] = message
            elif kind_upper == "VIDEO":
                endpoint = f"/{page_id}/videos"
                payload = {"file_url": media_url}
                if message:
                    payload["description"] = message
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported FB media kind '{media_kind}'",
                )
        else:
            endpoint = f"/{page_id}/feed"
            payload = {"message": message}
            if link:
                payload["link"] = link

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                _graph_url(endpoint),
                params={"access_token": page_access_token},
                json=payload,
            )
        body = resp.json()
        if resp.status_code >= 400:
            err = body.get("error", {}) or {}
            logger.error(
                "FB post publish failed status=%s endpoint=%s body=%s",
                resp.status_code,
                endpoint,
                body,
            )
            parts = [err.get("message") or "unknown error"]
            if err.get("code") is not None:
                parts.append(f"code={err.get('code')}")
            if err.get("error_subcode") is not None:
                parts.append(f"subcode={err.get('error_subcode')}")
            if err.get("fbtrace_id"):
                parts.append(f"trace={err.get('fbtrace_id')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FB post publish failed: " + " | ".join(parts),
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
        graph_base: str | None = None,
    ) -> dict[str, Any]:
        """Synchronous IG publish — creates the media container, polls until
        Meta finishes processing it, then publishes. Caller's workflow run
        blocks for `max_poll_seconds` worst case. Suitable for image posts
        and short videos; for large videos / Reels, switch to an async
        worker pattern (PR C scope).
        """
        import asyncio

        base = graph_base or f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}"
        kind_upper = kind.upper()
        params: dict[str, Any] = {"access_token": page_access_token}
        # Meta's v20+ /media container endpoint requires `media_type` on
        # every call — older deployments could omit it for image posts
        # and Meta would default to IMAGE, but current versions reject
        # the call ("Only photo or video can be accepted as media type")
        # when media_type is absent. Always send it; pair with the right
        # url field for the asset kind.
        params["media_type"] = kind_upper
        if kind_upper == "IMAGE":
            params["image_url"] = media_url
        else:
            params["video_url"] = media_url
        if caption is not None:
            params["caption"] = caption
        if kind_upper == "STORIES":
            # Stories accept either image_url or video_url; remove `caption`
            # since story containers don't take captions.
            params.pop("caption", None)

        async with httpx.AsyncClient(timeout=60.0) as client:
            container_resp = await client.post(
                f"{base}/{ig_user_id}/media",
                params=params,
            )
            container = container_resp.json()
            if container_resp.status_code >= 400 or "id" not in container:
                err = container.get("error", {}) or {}
                logger.error(
                    "IG media container failed status=%s ig_user_id=%s body=%s",
                    container_resp.status_code,
                    ig_user_id,
                    container,
                )
                parts = [err.get("message") or "unknown error"]
                if err.get("code") is not None:
                    parts.append(f"code={err.get('code')}")
                if err.get("error_subcode") is not None:
                    parts.append(f"subcode={err.get('error_subcode')}")
                if err.get("fbtrace_id"):
                    parts.append(f"trace={err.get('fbtrace_id')}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="IG media container failed: " + " | ".join(parts),
                )
            creation_id = container["id"]

            # Poll until FINISHED. Image posts usually return FINISHED on
            # the first call; videos take 5-30s. Bail with a clear error
            # if Meta returns ERROR.
            elapsed = 0
            poll_interval = 2
            while elapsed < max_poll_seconds:
                status_resp = await client.get(
                    f"{base}/{creation_id}",
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
                f"{base}/{ig_user_id}/media_publish",
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

    async def _credential_account_ids(self, credential_id_str: str) -> set[str]:
        """Return every id string that, through `credential_id`, could
        refer to the same account.

        Instagram exposes up to three distinct ids per business account
        (Login-scoped `id`, IG Graph `user_id`, Messaging-scoped id) and
        Meta's webhook envelope doesn't always echo the id the caller used
        to register the subscription. The webhook receiver folds all
        equivalent ids from the cred's stored profile data into one set
        and treats any match in the set as the same account — strict
        enough that two unrelated credentials can't claim each other's
        slots, loose enough to bridge the cross-namespace mismatch.
        """
        try:
            cred_uuid = _uuid.UUID(credential_id_str)
        except (ValueError, TypeError):
            return set()
        cred_service = CredentialService(self.db)
        cred = await cred_service.repo.get_by_id(cred_uuid)
        if cred is None:
            return set()
        data = await cred_service.get_decrypted_credential(cred) or {}
        ids: set[str] = set()
        for acc in data.get("ig_accounts") or []:
            if not isinstance(acc, dict):
                continue
            for k in ("id", "user_id"):
                v = acc.get(k)
                if v:
                    ids.add(str(v))
        for p in data.get("pages") or []:
            if not isinstance(p, dict):
                continue
            pid = p.get("id")
            if pid:
                ids.add(str(pid))
            ig = p.get("instagram_business_account") or {}
            ig_id = ig.get("id")
            if ig_id:
                ids.add(str(ig_id))
        return ids

    async def _claim_slots_with_id_fallback(
        self,
        object_type: str,
        target_id: str,
        field: str,
    ) -> list:
        """Cred-aware id-namespace fallback.

        Called only when the exact `(object, target_id, field)` slot
        lookup returned nothing. Lists every open slot waiting on
        `(object, field)`, resolves each slot's credential to its full
        account-id-set, and atomically claims the slots whose cred
        considers `target_id` one of its accounts.

        Special-cases Meta's "Send Test Event" delivery (entry.id == "0")
        — that payload carries no real account binding, so we accept any
        slot for `(object, field)` regardless of its cred.
        """
        from apps.api.app.features.triggers.listen_service import (
            claim_slot,
            list_slots_for_event,
        )

        candidates = await list_slots_for_event(object_type, field)
        if not candidates:
            return []

        is_meta_test = target_id == "0"
        loose = bool(getattr(settings, "META_WEBHOOK_LOOSE_LISTEN_MATCH", False))
        claimed: list = []
        for cand in candidates:
            if is_meta_test or loose:
                # Meta test envelope carries no real id; loose mode is an
                # explicit dev-only opt-in for the same effect.
                if await claim_slot(cand):
                    claimed.append(cand)
                continue
            if not cand.credential_id:
                continue
            account_ids = await self._credential_account_ids(cand.credential_id)
            if target_id not in account_ids:
                continue
            if await claim_slot(cand):
                claimed.append(cand)

        if claimed:
            logger.info(
                "Meta webhook id-namespace fallback claimed %d slot(s) "
                "(object=%s field=%s target_id=%s — exact match missed)",
                len(claimed),
                object_type,
                field,
                target_id,
            )
        return claimed

    async def receive_webhook(
        self,
        app_id: str,
        raw_body: bytes,
        signature: str | None,
    ) -> tuple[int, list[str]]:
        # Only accept events for a configured app. Two app ids are
        # supported: the Facebook app (META_APP_ID) for Page / Messenger /
        # WhatsApp / Lead Ads, and the standalone Instagram Login app
        # (META_INSTAGRAM_APP_ID) for IG-only deployments. Either one alone
        # is fine — rejecting unrecognized ids stops random callers from
        # poking the webhook endpoint.
        allowed_app_ids = {
            settings.META_APP_ID,
            settings.META_INSTAGRAM_APP_ID,
        }
        allowed_app_ids.discard("")
        allowed_app_ids.discard(None)
        if allowed_app_ids and app_id not in allowed_app_ids:
            raise HTTPException(status_code=404, detail="Unknown Meta app id")

        if not verify_webhook_signature(raw_body, signature, app_id):
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
        logger.info(
            "Meta webhook raw payload object=%s entries=%s",
            object_type,
            json.dumps(entries),
        )

        # Lazy-import to dodge circular: triggers → workflows → executions.
        from apps.api.app.execution_engine.engine import execution_engine
        from apps.api.app.features.meta.repository import MetaSubscriptionRepository
        from apps.api.app.features.triggers.listen_service import (
            claim_slots_for_event,
        )
        from apps.api.app.features.triggers.repository import TriggerFixtureRepository
        from apps.api.app.features.workflows.repository import WorkflowRepository

        sub_repo = MetaSubscriptionRepository(self.db)
        wf_repo = WorkflowRepository(self.db)
        fixture_repo = TriggerFixtureRepository(self.db)
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

                logger.info(
                    "Meta webhook routing tuple: object=%s target_id=%s field=%s",
                    object_type,
                    target_id,
                    event["field"],
                )

                # ── Listen slots ─────────────────────────────────────
                # Fire any debug "Listen for next event" slots waiting
                # on this exact routing tuple, BEFORE production
                # subscription dispatch. Slots are single-shot and
                # claimed atomically; firing one does NOT suppress the
                # normal subscription path below — both are independent
                # observers of the same event.
                trigger_payload = {
                    "object": object_type,
                    "field": event["field"],
                    "target_id": target_id,
                    "value": event["value"],
                    "received_at": entry.get("time"),
                }
                try:
                    slots = await claim_slots_for_event(object_type, target_id, event["field"])
                    if not slots:
                        slots = await self._claim_slots_with_id_fallback(
                            object_type, target_id, event["field"]
                        )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"Meta webhook: listen-slot claim failed ({exc})")
                    slots = []
                for slot in slots:
                    try:
                        wf = await wf_repo.get_by_id(_uuid.UUID(slot.workflow_id))
                        if wf is None:
                            continue
                        await execution_engine.dispatch_existing(
                            execution_id=_uuid.UUID(slot.execution_id),
                            workflow_id=wf.id,
                            graph=wf.graph,
                            trigger_type="listen",
                            input_data=trigger_payload,
                        )
                        execution_ids.append(slot.execution_id)
                        triggered += 1
                    except Exception as exc:  # noqa: BLE001
                        logger.exception(
                            f"Meta webhook: listen-slot dispatch failed "
                            f"workflow={slot.workflow_id} execution={slot.execution_id}: {exc}"
                        )

                # ── Production subscriptions ─────────────────────────
                # DB-indexed routing — composite index on
                # (object_type, target_id, field) makes this O(log N).
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
                        continue

                    # Pin payload to the trigger node so the editor can
                    # replay it on a manual Run. Best-effort — pinning
                    # failure must not break a successful dispatch.
                    try:
                        await fixture_repo.upsert(
                            workflow_id=wf.id,
                            workspace_id=wf.workspace_id,
                            node_id=sub.node_id,
                            payload=trigger_payload,
                            source="meta",
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            f"Meta webhook: fixture upsert failed for "
                            f"workflow={wf.id} node={sub.node_id}: {exc}"
                        )

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
            elif item in ("post", "status", "share", "photo", "video"):
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

    # Meta wraps text DMs in either `message` (new) or `message_edit` (edited
    # within the 15-minute edit window). Both carry the same intent — a text
    # message landed in the conversation — so the trigger fires for both.
    message = msg.get("message") or msg.get("message_edit")
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


# (object, synthesized_field) → (consolidated trigger node type, event_type).
# Consolidated nodes carry an `event_type` dropdown — webhook routing now
# names the surface-level trigger node (e.g. `trigger.meta.instagram`)
# and a `_FIELD_TO_EVENT` lookup tells the matcher which event_type that
# entry corresponds to. The MetaSubscription row already carries the raw
# `field`, so DB lookups remain unchanged.
_TRIGGER_MAP: dict[tuple[str, str], tuple[str, str]] = {
    # Instagram
    ("instagram", "comments"): ("trigger.meta.instagram", "comment"),
    ("instagram", "mentions"): ("trigger.meta.instagram", "mention"),
    ("instagram", "messaging.text"): ("trigger.meta.instagram", "message"),
    ("instagram", "messaging.ig_story_reply"): ("trigger.meta.instagram", "story_reply"),
    ("instagram", "messaging.ig_story_mention"): ("trigger.meta.instagram", "story_mention"),
    # Facebook Page / Messenger
    ("page", "messaging.text"): ("trigger.meta.facebook", "message"),
    ("page", "messaging.postback"): ("trigger.meta.facebook", "postback"),
    ("page", "feed.comment"): ("trigger.meta.facebook", "comment"),
    ("page", "feed.reaction"): ("trigger.meta.facebook", "reaction"),
    ("page", "mention"): ("trigger.meta.facebook", "mention"),
    # Lead Ads (delivered under the `page` object — consolidated separately
    # from the Facebook trigger because the surface, credentials, and
    # downstream resource picker semantics all differ).
    ("page", "leadgen"): ("trigger.meta.lead", "submission"),
    # WhatsApp Cloud API — split inside _flatten_entry into one event
    # per inbound message (`wa.messages`) or status callback (`wa.statuses`).
    ("whatsapp_business_account", "wa.messages"): ("trigger.meta.whatsapp", "message"),
    ("whatsapp_business_account", "wa.statuses"): ("trigger.meta.whatsapp", "status"),
}


# Reverse lookup used by `_scan_meta_triggers`: given a consolidated
# trigger node + the `event_type` chosen by the user, return the
# webhook routing tuple (object_type, field) that the MetaSubscription
# row must be keyed on.
_EVENT_TO_FIELD: dict[str, dict[str, tuple[str, str]]] = {}
for _key, _value in _TRIGGER_MAP.items():
    _obj, _field = _key
    _node_type, _event_type = _value
    _EVENT_TO_FIELD.setdefault(_node_type, {})[_event_type] = (_obj, _field)


def _trigger_type_for(object_type: str | None, field: str) -> str | None:
    if not object_type:
        return None
    pair = _TRIGGER_MAP.get((object_type, field))
    if pair is None:
        return None
    return pair[0]


# Per-trigger property filter so webhook routing only fires the workflow
# whose trigger node points at the *same* target id Meta delivered the
# event for. Keys are the consolidated node types — each surface only
# binds one resource kind regardless of which event was selected.
_TARGET_FILTER_BY_TRIGGER: dict[str, str] = {
    "trigger.meta.instagram": "ig_account_id",
    "trigger.meta.facebook": "page_id",
    "trigger.meta.lead": "page_id",
    "trigger.meta.whatsapp": "waba_id",
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


# Per-surface description of how to extract the routing tuple from a
# consolidated trigger node's saved properties. `field` is omitted here
# because it depends on the user-picked `event_type` — `_scan_meta_triggers`
# resolves it via `_EVENT_TO_FIELD`. Keeps `sync_workflow_subscriptions`
# generic; adding a Meta surface is one entry here.
_TRIGGER_SPECS: dict[str, dict[str, str]] = {
    "trigger.meta.instagram": {
        "object_type": "instagram",
        "target_prop": "ig_account_id",
    },
    "trigger.meta.facebook": {
        "object_type": "page",
        "target_prop": "page_id",
    },
    "trigger.meta.lead": {
        "object_type": "page",
        "target_prop": "page_id",
    },
    "trigger.meta.whatsapp": {
        "object_type": "whatsapp_business_account",
        "target_prop": "waba_id",
    },
}


# Self-check: every consolidated trigger node type in _EVENT_TO_FIELD
# must exist in _TRIGGER_SPECS with a matching object_type. Triggers at
# import so a desynced edit fails pytest collection instead of swallowing
# webhooks at runtime.
for _trigger_type, _event_map in _EVENT_TO_FIELD.items():
    _spec = _TRIGGER_SPECS.get(_trigger_type)
    if _spec is None:
        raise RuntimeError(
            f"_EVENT_TO_FIELD references {_trigger_type!r} but _TRIGGER_SPECS has no entry"
        )
    for _event_type, (_obj, _field) in _event_map.items():
        if _obj != _spec["object_type"]:
            raise RuntimeError(
                f"_TRIGGER_SPECS / _TRIGGER_MAP drift: {_trigger_type}/{_event_type} → "
                f"object={_obj} but spec says {_spec['object_type']!r}"
            )


def _scan_meta_triggers(workflow: Any) -> list[dict[str, Any]]:
    """Pull every `trigger.meta.*` node out of a workflow graph alongside
    its saved properties + the routing spec we'll use to build a row.

    Consolidated triggers carry an `event_type` property; the (object,
    field) tuple for the MetaSubscription row is derived from
    `_EVENT_TO_FIELD[node_type][event_type]`. A node with no / unknown
    event_type is skipped so a half-configured trigger doesn't create a
    stranded routing row.
    """
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
        event_map = _EVENT_TO_FIELD.get(node_type) or {}
        if not event_map:
            continue
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        props = (node.get("data") or {}).get("properties") or {}
        event_type = str(props.get("event_type") or "").strip()
        if not event_type or event_type not in event_map:
            continue
        _, field = event_map[event_type]
        target_id = str(props.get(spec["target_prop"]) or "").strip()
        credential_id = str(props.get("credential") or "").strip()
        out.append(
            {
                "node_id": node_id,
                "trigger_type": node_type,
                "object_type": spec["object_type"],
                "field": field,
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

        # Postback triggers need a Get Started button on the Page so the
        # first conversation tap dispatches a `messaging_postback` event.
        # Best-effort + idempotent — Meta no-ops the call when the same
        # payload is already installed.
        if upserted.object_type == "page" and upserted.field == "messaging.postback":
            try:
                from apps.api.app.features.credentials.service import CredentialService
                from apps.api.app.node_system.nodes.meta._helpers import page_token_by_page_id

                cred_service = CredentialService(db)
                cred = await cred_service.repo.get_by_id_and_workspace(
                    upserted.credential_id, upserted.workspace_id
                )
                if cred is not None:
                    cred_data = await cred_service.get_decrypted_credential(cred)
                    page_token = page_token_by_page_id(cred_data, upserted.target_id)
                    if page_token:
                        await MetaService(db).register_messenger_get_started(
                            page_access_token=page_token,
                            page_id=upserted.target_id,
                        )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Messenger get_started auto-setup failed for workflow=%s page=%s: %s",
                    workflow.id,
                    upserted.target_id,
                    exc,
                )

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


async def register_meta_subscription(
    db: AsyncSession,
    *,
    credential_id: _uuid.UUID,
    workspace_id: _uuid.UUID,
    object_type: str,
    target_id: str,
) -> None:
    """POST `subscribed_apps` to Meta so events for `target_id` start
    flowing to our webhook endpoint.

    Three credential / object-type combinations are handled:

      1. `meta_oauth` + page / instagram via Page: hits
         `graph.facebook.com/{page_id}/subscribed_apps` with the page
         access token. IG events flow through the linked Page's
         subscription.
      2. `meta_oauth` + whatsapp_business_account: hits
         `graph.facebook.com/{waba_id}/subscribed_apps` with the user
         long-lived token.
      3. `instagram_oauth` + instagram: hits
         `graph.instagram.com/{ig_user_id}/subscribed_apps` with the IG
         user token. No Page involved.

    Idempotent on Meta's side — re-subscribing an already-subscribed
    target succeeds. Exposed publicly so the listen-slot endpoint can
    register on behalf of an inactive workflow (so the user can debug
    without flipping the workflow live).

    Failures bubble up to the caller.
    """
    from apps.api.app.features.credentials.service import CredentialService

    cred_service = CredentialService(db)
    credential = await cred_service.repo.get_by_id_and_workspace(credential_id, workspace_id)
    if credential is None:
        raise ValueError("Meta credential not found")
    data = await cred_service.get_decrypted_credential(credential)
    cred_type = credential.type or ""

    # Standalone Instagram Login — own Graph host + own subscribed_apps shape.
    if cred_type == "instagram_oauth" and object_type == "instagram":
        accounts = (data or {}).get("ig_accounts") or []
        ig_token: str | None = None
        for acc in accounts:
            if not isinstance(acc, dict):
                continue
            if str(acc.get("id") or "") == target_id:
                token = acc.get("access_token")
                if isinstance(token, str) and token:
                    ig_token = token
                break
        if not ig_token:
            ig_token = str((data or {}).get("access_token") or "") or None
        if not ig_token:
            raise ValueError("Instagram credential missing access token")
        version = settings.META_GRAPH_API_VERSION
        url = f"https://graph.instagram.com/{version}/{target_id}/subscribed_apps"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                url,
                params={
                    "subscribed_fields": (
                        "comments,messages,mentions,live_comments,messaging_postbacks"
                    ),
                },
                headers={"Authorization": f"Bearer {ig_token}"},
            )
        body = resp.json()
        if resp.status_code >= 400 or not body.get("success", True):
            err = body.get("error", {}) or {}
            logger.error(
                "Instagram subscribed_apps failed (status=%s) target=%s body=%s",
                resp.status_code,
                target_id,
                body,
            )
            parts = [err.get("message") or "unknown error"]
            if err.get("code") is not None:
                parts.append(f"code={err.get('code')}")
            if err.get("error_subcode") is not None:
                parts.append(f"subcode={err.get('error_subcode')}")
            if err.get("error_user_msg"):
                parts.append(f"user_msg={err.get('error_user_msg')}")
            if err.get("fbtrace_id"):
                parts.append(f"trace={err.get('fbtrace_id')}")
            raise ValueError("Instagram subscribed_apps failed: " + " | ".join(parts))
        return

    if object_type == "whatsapp_business_account":
        access_token = str((data or {}).get("access_token") or "")
        if not access_token:
            raise ValueError("Meta credential missing access_token for WhatsApp subscribe")
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                _graph_url(f"/{target_id}/subscribed_apps"),
                headers={"Authorization": f"Bearer {access_token}"},
            )
        body = resp.json()
        if resp.status_code >= 400 or not body.get("success", True):
            err = body.get("error", {})
            raise ValueError(f"WhatsApp subscribe_apps failed: {err.get('message') or body}")
        return

    # meta_oauth — Page / Instagram. IG events flow through the linked
    # Page's subscribed_apps registration.
    pages = (data or {}).get("pages") or []
    page_token: str | None = None
    page_target_id: str | None = None
    if object_type == "page":
        for p in pages:
            if isinstance(p, dict) and str(p.get("id") or "") == target_id:
                token = p.get("access_token")
                if isinstance(token, str) and token:
                    page_token = token
                page_target_id = target_id
                break
    else:  # instagram — find the Page that owns this IG business account
        for p in pages:
            if not isinstance(p, dict):
                continue
            ig = p.get("instagram_business_account") or {}
            if str(ig.get("id") or "") == target_id:
                token = p.get("access_token")
                if isinstance(token, str) and token:
                    page_token = token
                page_target_id = str(p.get("id") or "")
                break
        if not page_target_id:
            raise ValueError("No Page linked to this Instagram account")

    if not page_token:
        raise ValueError("No page access token for this target")

    # Meta's v20+ Page subscribed_apps endpoint requires an explicit
    # `subscribed_fields` list — older calls that relied on the app's
    # webhook configuration to provide the default now fail with
    # "(#100) The parameter subscribed_fields is required."
    # The list below covers every Page / Messenger / IG-via-Page / Lead
    # Ads field Fuse triggers consume — subscribe broadly so a single
    # workflow activation doesn't have to re-call subscribed_apps for
    # each new trigger node type the same Page already owns.
    page_subscribed_fields = ",".join(
        [
            "feed",
            "mention",
            "messages",
            "messaging_postbacks",
            "message_reactions",
            "message_reads",
            "messaging_optins",
            "messaging_referrals",
            "leadgen",
        ]
    )
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            _graph_url(f"/{page_target_id}/subscribed_apps"),
            params={
                "access_token": page_token,
                "subscribed_fields": page_subscribed_fields,
            },
        )
    body = resp.json()
    if resp.status_code >= 400 or not body.get("success", True):
        err = body.get("error", {}) or {}
        logger.error(
            "Page subscribed_apps failed status=%s target=%s body=%s",
            resp.status_code,
            page_target_id,
            body,
        )
        parts = [err.get("message") or "unknown error"]
        if err.get("code") is not None:
            parts.append(f"code={err.get('code')}")
        if err.get("error_subcode") is not None:
            parts.append(f"subcode={err.get('error_subcode')}")
        if err.get("fbtrace_id"):
            parts.append(f"trace={err.get('fbtrace_id')}")
        raise ValueError("subscribed_apps failed: " + " | ".join(parts))


async def _meta_subscribe_target(db: AsyncSession, sub: Any) -> None:
    """Backwards-compatible wrapper for `sync_workflow_subscriptions`.
    Lifts the routing tuple off a MetaSubscription row + delegates to
    `register_meta_subscription`."""
    await register_meta_subscription(
        db,
        credential_id=sub.credential_id,
        workspace_id=sub.workspace_id,
        object_type=sub.object_type,
        target_id=sub.target_id,
    )
