from __future__ import annotations

import httpx

from apps.api.app.core.config import settings
from apps.api.app.credential_manager.oauth.base import (
    REDIRECT_URI,
    with_expiry_metadata,
)


class MicrosoftOAuthProvider:
    """Microsoft Graph OAuth — shared by Outlook, Teams, OneDrive,
    SharePoint, Excel, and Planner. Single grant covers all five Phase
    2.1 surfaces so the user only consents once per workspace.

    Tenant `common` accepts both Microsoft account (personal) tokens
    and any AAD-joined work account. Deployments that need to lock to
    a single tenant override `MICROSOFT_TENANT_ID`.
    """

    id = "microsoft_oauth"
    name = "Microsoft"
    icon_slug = "microsoft"
    color = "#ffffff"
    type = "oauth"
    brand = "microsoft"
    description = (
        "Connect Microsoft 365 for Outlook mail, Teams chat, OneDrive + "
        "SharePoint files, Excel workbooks, and Planner."
    )
    scopes = [
        "Read, send, and organize Outlook mail",
        "Read and send Teams chat messages + channel messages",
        "Read and write your OneDrive + SharePoint files",
        "Read and write Excel workbook ranges + tables",
        "Read and write Planner tasks",
        "Read your profile",
        "Keep the connection alive (offline access)",
    ]

    # Phase 4.28 — added `User.ReadWrite.All` + `Group.ReadWrite.All` for
    # the microsoft_ad (Entra ID) action node, and Dataverse `user_impersonation`
    # for the microsoft_dataverse action node. Both are feature-flagged since
    # they escalate the consent screen to admin-managed operations.
    @classmethod
    def _scope_str(cls) -> str:
        base = [
            "Mail.ReadWrite",
            "Mail.Send",
            "Chat.ReadWrite",
            "ChannelMessage.Send",
            "ChannelMessage.Read.All",
            "Team.ReadBasic.All",
            "Files.ReadWrite.All",
            "Sites.ReadWrite.All",
            "Tasks.ReadWrite",
            "User.Read",
            "offline_access",
        ]
        if getattr(settings, "MICROSOFT_ENTRA_ADMIN_ENABLED", False):
            base.append("User.ReadWrite.All")
            base.append("Group.ReadWrite.All")
            base.append("Directory.Read.All")
        if getattr(settings, "MICROSOFT_DATAVERSE_ENABLED", False):
            base.append("https://{org}.crm.dynamics.com/user_impersonation")
        return " ".join(base)

    _SCOPE_STR = ""  # kept for back-compat readers — real value from _scope_str()

    @classmethod
    def _tenant(cls) -> str:
        return getattr(settings, "MICROSOFT_TENANT_ID", None) or "common"

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": getattr(settings, "MICROSOFT_CLIENT_ID", "") or "",
            "redirect_uri": REDIRECT_URI.format(service="microsoft"),
            "response_type": "code",
            "scope": self._scope_str(),
            "response_mode": "query",
            "state": state,
            "prompt": "select_account",
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return (
            f"https://login.microsoftonline.com/{self._tenant()}"
            f"/oauth2/v2.0/authorize?{urlencode(params)}"
        )

    async def exchange_code(self, code, code_verifier=None):

        data: dict = {
            "client_id": getattr(settings, "MICROSOFT_CLIENT_ID", "") or "",
            "client_secret": getattr(settings, "MICROSOFT_CLIENT_SECRET", "") or "",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI.format(service="microsoft"),
            "scope": self._scope_str(),
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{self._tenant()}/oauth2/v2.0/token",
                data=data,
            )
        body = response.json()
        if "error" in body:
            raise ValueError(
                f"Microsoft OAuth failed: {body.get('error_description', body['error'])}"
            )
        return with_expiry_metadata(body)

    async def refresh_access_token(self, refresh_token: str):

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{self._tenant()}/oauth2/v2.0/token",
                data={
                    "client_id": getattr(settings, "MICROSOFT_CLIENT_ID", "") or "",
                    "client_secret": getattr(settings, "MICROSOFT_CLIENT_SECRET", "") or "",
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": self._scope_str(),
                },
            )
        body = response.json()
        if "access_token" not in body:
            err = body.get("error_description") or body.get("error") or body
            raise ValueError(f"Microsoft token refresh failed: {err}")
        return with_expiry_metadata(body)


PROVIDER = MicrosoftOAuthProvider()
