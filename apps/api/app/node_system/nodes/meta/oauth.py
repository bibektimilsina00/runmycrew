from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.core.config import settings
from apps.api.app.credential_manager.oauth.base import (
    REDIRECT_URI,
    with_expiry_metadata,
)


class MetaOAuthProvider:
    """OAuth provider for the entire Meta (Facebook / Instagram / WhatsApp /
    Messenger) product family.

    All five surfaces sit behind one Meta developer app and one Graph API
    endpoint. We request the union of permissions upfront so the same
    `meta_oauth` credential can power FB Page, IG comment/DM, WhatsApp, and
    Lead Ads nodes — the user picks the *resource* (Page / IG user / WABA /
    form) per node via a `meta-resource` field type, not per credential.

    Token shape after `exchange_code`:
      access_token: long-lived user token (~60 days)
      token_type:   'bearer'
      expires_in:   seconds (Meta returns int)
      user_id:      Facebook user id
      pages:        list of {id, name, access_token, category} — page tokens
                    derived in the same exchange so node code never has to
                    re-fetch them. Page tokens don't expire unless the user
                    revokes the app.
    """

    id = "meta_oauth"
    name = "Meta (Facebook, Instagram, WhatsApp)"
    icon_slug = "meta"
    color = "#ffffff"
    type = "oauth"
    brand = "meta"
    description = (
        "Connect Facebook Pages, Instagram Business, WhatsApp Business, and "
        "Lead Ads in one credential."
    )
    scopes = [
        "Manage Facebook Pages + post on your behalf",
        "Read + reply to Page comments and mentions",
        "Send and receive Messenger and Instagram DMs",
        "Read + reply to Instagram comments; publish posts and stories",
        "Read insights for Pages and Instagram posts",
        "Read + reply to WhatsApp Business messages and templates",
        "Retrieve Lead Ads form submissions",
    ]

    def _graph_url(self, path: str) -> str:
        return f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}{path}"

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        if not settings.META_FB_LOGIN_CONFIG_ID:
            raise ValueError(
                "META_FB_LOGIN_CONFIG_ID is not set. Create a Configuration in "
                "Meta App Dashboard → Facebook Login for Business → Configurations, "
                "then paste the id into the env var."
            )

        # Facebook Login for Business drives the permission set and asset
        # picker from the Configuration referenced by `config_id`. Meta's
        # web dialog ignores any `scope` query param when `config_id` is
        # present, so we never send one.
        # Meta's OAuth dialog supports PKCE only on the mobile SDK — the
        # web flow ignores `code_challenge`, so skip it here to keep parity
        # with what their docs actually accept.
        params: dict[str, str] = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": REDIRECT_URI.format(service="meta"),
            "state": state,
            "response_type": "code",
            "config_id": settings.META_FB_LOGIN_CONFIG_ID,
        }
        return f"https://www.facebook.com/{settings.META_GRAPH_API_VERSION}/dialog/oauth?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Step 1 — short-lived user token (1-2 hours).
            short = await client.get(
                self._graph_url("/oauth/access_token"),
                params={
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "redirect_uri": REDIRECT_URI.format(service="meta"),
                    "code": code,
                },
            )
            short_data = short.json()
            if "access_token" not in short_data:
                err = short_data.get("error", {})
                raise ValueError(f"Meta OAuth failed: {err.get('message') or short_data}")

            # Step 2 — exchange for a long-lived user token (~60 days).
            long_resp = await client.get(
                self._graph_url("/oauth/access_token"),
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "fb_exchange_token": short_data["access_token"],
                },
            )
            long_data = long_resp.json()
            if "access_token" not in long_data:
                err = long_data.get("error", {})
                raise ValueError(
                    f"Meta long-lived token exchange failed: {err.get('message') or long_data}"
                )
            user_token = long_data["access_token"]

            # Step 3 — fetch the FB user id (used as display + logging key).
            me = await client.get(
                self._graph_url("/me"),
                params={"access_token": user_token, "fields": "id,name"},
            )
            me_data = me.json()
            if "id" not in me_data:
                raise ValueError("Meta /me lookup missing id")

            # Step 4 — fetch every Page the user manages plus the
            # corresponding (non-expiring) page tokens. Includes IG business
            # account id when one is linked to the Page.
            pages_resp = await client.get(
                self._graph_url(f"/{me_data['id']}/accounts"),
                params={
                    "access_token": user_token,
                    "fields": "id,name,category,access_token,instagram_business_account{id,username}",
                    "limit": 100,
                },
            )
            pages_data = pages_resp.json()
            pages = pages_data.get("data", [])

            # Step 5 — fetch every WhatsApp Business Account (WABA) the user
            # owns plus the registered phone numbers underneath each one.
            # Mirrors the page-enrichment hop above: nodes can read WABA +
            # phone metadata straight from credential storage instead of
            # round-tripping the Graph API on every send. Failures here are
            # non-fatal — Pages-only setups still work; only WhatsApp nodes
            # would surface "no WABAs" later.
            waba_accounts: list[dict[str, Any]] = []
            try:
                biz_resp = await client.get(
                    self._graph_url(f"/{me_data['id']}/businesses"),
                    params={
                        "access_token": user_token,
                        "fields": (
                            "id,name,"
                            "owned_whatsapp_business_accounts"
                            "{id,name,phone_numbers"
                            "{id,display_phone_number,verified_name,quality_rating}}"
                        ),
                        "limit": 50,
                    },
                )
                biz_data = biz_resp.json()
                for biz in biz_data.get("data", []) or []:
                    owned = (biz.get("owned_whatsapp_business_accounts") or {}).get("data") or []
                    for waba in owned:
                        # Inline business id so the resource picker can
                        # display "WABA · Business" without another hop.
                        waba["business_id"] = biz.get("id")
                        waba["business_name"] = biz.get("name")
                        waba_accounts.append(waba)
            except Exception:  # noqa: BLE001 — enrichment is best-effort
                waba_accounts = []

        return with_expiry_metadata(
            {
                "access_token": user_token,
                "token_type": "bearer",
                "expires_in": long_data.get("expires_in"),
                "user_id": me_data["id"],
                "user_name": me_data.get("name"),
                "pages": pages,
                "whatsapp_business_accounts": waba_accounts,
            }
        )

    async def refresh_access_token(self, refresh_token: str):
        # Meta long-lived user tokens are refreshed by exchanging the *current*
        # long-lived token (passed in as `refresh_token` here) for a new
        # 60-day token via the same `fb_exchange_token` endpoint. There is
        # no separate refresh token in Meta's flow.

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                self._graph_url("/oauth/access_token"),
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "fb_exchange_token": refresh_token,
                },
            )
            data = resp.json()
        if "access_token" not in data:
            err = data.get("error", {})
            raise ValueError(f"Meta token refresh failed: {err.get('message') or data}")
        return with_expiry_metadata(data)


PROVIDER = MetaOAuthProvider()
