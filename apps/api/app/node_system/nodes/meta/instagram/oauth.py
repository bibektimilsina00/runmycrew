from __future__ import annotations

import httpx

from apps.api.app.core.config import settings
from apps.api.app.credential_manager.oauth.base import (
    REDIRECT_URI,
    with_expiry_metadata,
)


class InstagramOAuthProvider:
    """OAuth provider for the standalone Instagram API (Instagram Login).

    Use this when the user has an Instagram Business / Creator account but
    no Facebook Page (or doesn't want to link one). It uses Meta's
    *Instagram Login* path — a sibling Meta app under the same Meta App
    Dashboard, with its own app id / secret and OAuth dialog hosted at
    `api.instagram.com`.

    Token shape after `exchange_code`:
      access_token: long-lived IG user token (~60 days, refreshable
                    indefinitely as long as it's used ≥ once / 60 days)
      token_type:   'bearer'
      expires_in:   seconds
      user_id:      IG numeric user id (same value Meta calls `user_id`
                    inside the IG OAuth response)
      ig_accounts:  list of {id, username, account_type} — always a single
                    entry today (IG Login authorises one IG account at a
                    time). Stored as a list so the resource picker code
                    can share shape with `pages` from MetaOAuthProvider.
    """

    id = "instagram_oauth"
    name = "Instagram (standalone)"
    icon_slug = "instagram"
    color = "#ffffff"
    type = "oauth"
    brand = "meta"
    description = (
        "Connect an Instagram Business / Creator account directly, without a "
        "Facebook Page. Powers IG comment / DM / mention nodes."
    )
    scopes = [
        "Read your Instagram Business profile + media",
        "Read + reply to comments on your posts and reels",
        "Send and receive Instagram Direct Messages",
        "Read Instagram insights",
        "Publish posts and stories",
    ]

    # Scopes accepted by api.instagram.com/oauth/authorize. These are the
    # *new* (2024+) Instagram API scope names — note the `business_` prefix.
    _scopes = ",".join(
        [
            "instagram_business_basic",
            "instagram_business_manage_comments",
            "instagram_business_manage_messages",
            "instagram_business_content_publish",
            "instagram_business_manage_insights",
        ]
    )

    def _graph_url(self, path: str) -> str:
        # Instagram Login uses graph.instagram.com (NOT graph.facebook.com).
        return f"https://graph.instagram.com/{settings.META_GRAPH_API_VERSION}{path}"

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        if not settings.META_INSTAGRAM_APP_ID:
            raise ValueError(
                "META_INSTAGRAM_APP_ID is not set. Capture it from Meta App "
                "Dashboard → Instagram → API setup with Instagram login."
            )

        params: dict[str, str] = {
            "client_id": settings.META_INSTAGRAM_APP_ID,
            "redirect_uri": REDIRECT_URI.format(service="instagram"),
            "scope": self._scopes,
            "response_type": "code",
            "state": state,
        }
        return f"https://api.instagram.com/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Step 1 — short-lived IG user token (1 hour).
            short = await client.post(
                "https://api.instagram.com/oauth/access_token",
                data={
                    "client_id": settings.META_INSTAGRAM_APP_ID,
                    "client_secret": settings.META_INSTAGRAM_APP_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI.format(service="instagram"),
                    "code": code,
                },
            )
            short_data = short.json()
            if "access_token" not in short_data:
                err = short_data.get("error_message") or short_data.get("error") or short_data
                raise ValueError(f"Instagram OAuth failed: {err}")
            short_token = short_data["access_token"]
            ig_user_id = str(short_data.get("user_id") or "")

            # Step 2 — exchange for a long-lived token (~60 days).
            long_resp = await client.get(
                self._graph_url("/access_token"),
                params={
                    "grant_type": "ig_exchange_token",
                    "client_secret": settings.META_INSTAGRAM_APP_SECRET,
                    "access_token": short_token,
                },
            )
            long_data = long_resp.json()
            if "access_token" not in long_data:
                err = long_data.get("error", {})
                raise ValueError(
                    f"Instagram long-lived token exchange failed: {err.get('message') or long_data}"
                )
            user_token = long_data["access_token"]

            # Step 3 — fetch IG profile metadata (id, username, account type).
            me = await client.get(
                self._graph_url("/me"),
                params={
                    "access_token": user_token,
                    "fields": "id,user_id,username,account_type,name,profile_picture_url",
                },
            )
            me_data = me.json()
            if "id" not in me_data:
                err = me_data.get("error", {})
                raise ValueError(f"Instagram /me lookup failed: {err.get('message') or me_data}")

        ig_account = {
            "id": str(me_data["id"]),
            # `user_id` is the IG business account numeric id used by some
            # downstream endpoints (e.g. webhook subscription); `id` is the
            # Instagram Graph API user node id used for /messages etc.
            "user_id": str(me_data.get("user_id") or ig_user_id or me_data["id"]),
            "username": me_data.get("username"),
            "account_type": me_data.get("account_type"),
            "name": me_data.get("name"),
            "profile_picture_url": me_data.get("profile_picture_url"),
            "access_token": user_token,
        }

        return with_expiry_metadata(
            {
                "access_token": user_token,
                "token_type": "bearer",
                "expires_in": long_data.get("expires_in"),
                "user_id": ig_account["id"],
                "user_name": ig_account.get("username"),
                # Mirrors MetaOAuthProvider's `pages` shape so list_resources
                # can iterate one structure regardless of credential type.
                "ig_accounts": [ig_account],
            }
        )

    async def refresh_access_token(self, refresh_token: str):
        # Instagram long-lived tokens are refreshed by passing the *current*
        # long-lived token to ig_refresh_token. No separate refresh token.

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                self._graph_url("/refresh_access_token"),
                params={
                    "grant_type": "ig_refresh_token",
                    "access_token": refresh_token,
                },
            )
            data = resp.json()
        if "access_token" not in data:
            err = data.get("error", {})
            raise ValueError(f"Instagram token refresh failed: {err.get('message') or data}")
        return with_expiry_metadata(data)


PROVIDER = InstagramOAuthProvider()
