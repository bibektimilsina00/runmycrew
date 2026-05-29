from datetime import UTC, datetime, timedelta

from apps.api.app.core.config import settings
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

REDIRECT_URI = f"{settings.BASE_URL}/api/v1/credentials/oauth/{{service}}/callback"


def with_expiry_metadata(token_data: dict) -> dict:
    """Attach absolute expiry timestamps when OAuth responses include lifetimes."""
    now = datetime.now(UTC)
    enriched = dict(token_data)
    expires_in = enriched.get("expires_in")
    if isinstance(expires_in, int):
        enriched["expires_at"] = (now + timedelta(seconds=expires_in)).isoformat()
    refresh_expires_in = enriched.get("refresh_token_expires_in")
    if isinstance(refresh_expires_in, int):
        enriched["refresh_token_expires_at"] = (
            now + timedelta(seconds=refresh_expires_in)
        ).isoformat()
    return enriched


class SlackOAuthProvider:
    id = "slack_oauth"
    name = "Slack"
    type = "oauth"
    description = "Connect to your Slack workspace using OAuth 2.0"
    icon_url = "https://cdn.brandfetch.io/slack.com/icon"
    scopes = [
        "Send messages to channels",
        "Read public and private channels",
        "View users and email addresses",
        "Manage reactions",
        "Read and upload files",
    ]

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.SLACK_CLIENT_ID,
            "scope": "chat:write,channels:read,groups:read,im:read,mpim:read,users:read,users:read.email,reactions:read,reactions:write,files:read,files:write",
            "redirect_uri": REDIRECT_URI.format(service="slack"),
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        data = {
            "client_id": settings.SLACK_CLIENT_ID,
            "client_secret": settings.SLACK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI.format(service="slack"),
        }
        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data=data,
            )
        data = response.json()
        if not data.get("ok"):
            raise ValueError(f"Slack OAuth failed: {data.get('error')}")

        # Slack v2 can return token at root (bot token) or in authed_user (user token)
        access_token = data.get("access_token") or data.get("authed_user", {}).get("access_token")

        if not access_token:
            raise ValueError("Slack response missing access_token")

        return with_expiry_metadata(
            {
                "access_token": access_token,
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "team_id": data.get("team", {}).get("id"),
                "team_name": data.get("team", {}).get("name"),
            }
        )

    async def refresh_access_token(self, refresh_token: str):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": settings.SLACK_CLIENT_ID,
                    "client_secret": settings.SLACK_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
        data = response.json()
        if not data.get("ok"):
            raise ValueError(f"Slack token refresh failed: {data.get('error')}")
        return with_expiry_metadata(data)


class GitHubOAuthProvider:
    id = "github_oauth"
    name = "GitHub"
    type = "oauth"
    description = "Connect to GitHub using OAuth 2.0"
    icon_url = "https://cdn.brandfetch.io/github.com/icon"
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
        import httpx

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
        import httpx

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


class NotionOAuthProvider:
    id = "notion_oauth"
    name = "Notion"
    type = "oauth"
    description = "Connect to Notion using OAuth 2.0 (requires a public integration)"
    icon_url = "https://cdn.brandfetch.io/notion.so/icon"
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

        import httpx

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


class GoogleOAuthProvider:
    id = "google_oauth"
    name = "Google"
    type = "oauth"
    description = "Connect Google account for Gmail, Drive, and other Google services"
    icon_url = "https://cdn.brandfetch.io/google.com/icon"
    scopes = ["Read and send Gmail", "Access Google profile"]

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID if hasattr(settings, "GOOGLE_CLIENT_ID") else "",
            "redirect_uri": REDIRECT_URI.format(service="google"),
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly openid email profile",
            "access_type": "offline",
            "state": state,
            "prompt": "consent",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID
                    if hasattr(settings, "GOOGLE_CLIENT_ID")
                    else "",
                    "client_secret": settings.GOOGLE_CLIENT_SECRET
                    if hasattr(settings, "GOOGLE_CLIENT_SECRET")
                    else "",
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI.format(service="google"),
                },
            )
        data = response.json()
        if "error" in data:
            raise ValueError(f"Google OAuth failed: {data.get('error_description', data['error'])}")
        return with_expiry_metadata(data)

    async def refresh_access_token(self, refresh_token: str):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID
                    if hasattr(settings, "GOOGLE_CLIENT_ID")
                    else "",
                    "client_secret": settings.GOOGLE_CLIENT_SECRET
                    if hasattr(settings, "GOOGLE_CLIENT_SECRET")
                    else "",
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
        data = response.json()
        if "error" in data:
            raise ValueError(
                f"Google token refresh failed: {data.get('error_description', data['error'])}"
            )
        return with_expiry_metadata(data)


PROVIDERS = {
    "slack": SlackOAuthProvider(),
    "github": GitHubOAuthProvider(),
    "notion": NotionOAuthProvider(),
    "google": GoogleOAuthProvider(),
}


def get_oauth_provider(service_name: str):
    return PROVIDERS.get(service_name)
