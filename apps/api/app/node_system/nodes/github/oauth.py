from __future__ import annotations

import httpx

from apps.api.app.core.config import settings
from apps.api.app.credential_manager.oauth.base import (
    REDIRECT_URI,
    with_expiry_metadata,
)
from apps.api.app.node_system.nodes.github import COLOR, ICON_SLUG, NAME


class GitHubOAuthProvider:
    id = "github_oauth"
    name = NAME
    icon_slug = ICON_SLUG
    color = COLOR
    type = "oauth"
    description = "Connect to GitHub using OAuth 2.0"
    scopes = [
        "Full access to public and private repositories",
        "Read-only access to user profile information",
        "Manage organization memberships",
    ]

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "scope": "repo,user",
            "redirect_uri": REDIRECT_URI.format(service="github"),
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):

        data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI.format(service="github"),
        }
        # GitHub also supports PKCE, though we aren't using it yet
        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data=data,
            )
        data = response.json()
        if "error" in data:
            raise ValueError(f"GitHub OAuth failed: {data.get('error_description')}")

        return with_expiry_metadata(
            {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "refresh_token_expires_in": data.get("refresh_token_expires_in"),
                "token_type": data["token_type"],
                "scope": data["scope"],
            }
        )

    async def refresh_access_token(self, refresh_token: str):

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
        data = response.json()
        if "error" in data:
            raise ValueError(f"GitHub token refresh failed: {data.get('error_description')}")
        return with_expiry_metadata(data)


PROVIDER = GitHubOAuthProvider()
