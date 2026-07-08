from __future__ import annotations

import httpx

from apps.api.app.core.config import settings
from apps.api.app.credential_manager.oauth.base import (
    REDIRECT_URI,
    _SimpleOAuthProvider,
    with_expiry_metadata,
)


class DocuSignOAuthProvider(_SimpleOAuthProvider):
    """DocuSign OAuth. Uses `account.docusign.com` for prod OAuth
    authorization; deployments testing on the demo tenant override
    `DOCUSIGN_AUTH_HOST` to `account-d.docusign.com`.

    The API host itself is *per-account* (returned from userinfo after
    OAuth). The manifest resolves that URL via the credential's
    `account_url` field — same pattern as Shopify + Supabase.
    """

    id = "docusign_oauth"
    name = "DocuSign"
    icon_slug = "docusign"
    color = "#1c1c1c"
    description = "Connect DocuSign to send envelopes, manage templates, and pull signatures."
    scopes = [
        "Send and manage envelopes",
        "Read your DocuSign account + user info",
        "Sign requests on your behalf",
    ]
    _AUTH_URL = ""  # overridden per-instance via env
    _TOKEN_URL = ""
    _SCOPE_STR = "signature impersonation"
    _CLIENT_ID_ATTR = "DOCUSIGN_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "DOCUSIGN_CLIENT_SECRET"
    _REDIRECT_SERVICE = "docusign"

    @classmethod
    def _host(cls) -> str:
        # `account-d.docusign.com` for demo/dev; `account.docusign.com`
        # for prod. Env-driven so a single deployment can pick a tier.
        return getattr(settings, "DOCUSIGN_AUTH_HOST", None) or "account.docusign.com"

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
            "redirect_uri": REDIRECT_URI.format(service=self._REDIRECT_SERVICE),
            "response_type": "code",
            "scope": self._SCOPE_STR,
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return f"https://{self._host()}/oauth/auth?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):

        data: dict = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
            "client_secret": getattr(settings, self._CLIENT_SECRET_ATTR, "") or "",
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        async with httpx.AsyncClient() as client:
            response = await client.post(f"https://{self._host()}/oauth/token", data=data)
        body = response.json()
        if "error" in body:
            raise ValueError(
                f"DocuSign OAuth failed: {body.get('error_description', body['error'])}"
            )
        return with_expiry_metadata(body)

    async def refresh_access_token(self, refresh_token: str):

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self._host()}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
                    "client_secret": getattr(settings, self._CLIENT_SECRET_ATTR, "") or "",
                },
            )
        body = response.json()
        if "access_token" not in body:
            err = body.get("error_description") or body.get("error") or body
            raise ValueError(f"DocuSign token refresh failed: {err}")
        return with_expiry_metadata(body)


PROVIDER = DocuSignOAuthProvider()
