from __future__ import annotations

import httpx

from apps.api.app.core.config import settings
from apps.api.app.credential_manager.oauth.base import (
    REDIRECT_URI,
)


class NotionOAuthProvider:
    id = "notion_oauth"
    name = "Notion"
    icon_slug = "notion"
    color = "#ffffff"
    type = "oauth"
    description = "Connect to Notion using OAuth 2.0 (requires a public integration)"
    scopes = [
        "Read and create pages and databases",
        "Access workspace content shared with the integration",
    ]

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.NOTION_CLIENT_ID,
            "redirect_uri": REDIRECT_URI.format(service="notion"),
            "response_type": "code",
            "state": state,
            "owner": "user",
        }
        return f"https://api.notion.com/v1/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import base64

        credentials = base64.b64encode(
            f"{settings.NOTION_CLIENT_ID}:{settings.NOTION_CLIENT_SECRET}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.notion.com/v1/oauth/token",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json",
                },
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI.format(service="notion"),
                },
            )
        data = response.json()
        if "error" in data:
            raise ValueError(
                f"Notion OAuth failed: {data.get('error_description') or data['error']}"
            )

        return {
            "access_token": data["access_token"],
            "workspace_id": data.get("workspace_id"),
            "workspace_name": data.get("workspace_name"),
            "workspace_icon": data.get("workspace_icon"),
            "bot_id": data.get("bot_id"),
            "owner": data.get("owner"),
        }

    async def refresh_access_token(self, refresh_token: str):
        raise ValueError("Notion OAuth tokens do not expire and cannot be refreshed.")


PROVIDER = NotionOAuthProvider()
