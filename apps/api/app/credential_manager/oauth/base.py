"""Shared OAuth base classes + helpers.

`REDIRECT_URI`, `with_expiry_metadata`, `_SimpleOAuthProvider` — all pulled
out of the old monolith `flow.py` so per-node `oauth.py` files import them
from one place.
"""

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


class _SimpleOAuthProvider:
    """Boilerplate-light OAuth2 provider for vanilla Bearer-token flows.

    Subclasses set the five identity attributes (id, name, icon_slug,
    color, description, scopes), the two endpoints (`_AUTH_URL`,
    `_TOKEN_URL`), the scope string (`_SCOPE_STR`), and the env-var
    names + redirect service. Everything else (auth URL build, token
    exchange, refresh) is shared.

    Used for providers whose OAuth dance is the textbook flow: a code
    grant to a token endpoint, refresh-token rotation, no audience /
    PKCE-required / multi-tenant complications. Five Phase 2.2
    providers (Asana, HubSpot, Calendly, Zoom, Box) all fit this shape.
    """

    type = "oauth"
    # Subclass overrides — empty defaults keep the class instantiable
    # for type-checking but every real subclass replaces them.
    id: str = ""
    name: str = ""
    icon_slug: str | None = None
    color: str = "#1c1c1c"
    description: str = ""
    scopes: list[str] = []
    brand: str | None = None
    _AUTH_URL: str = ""
    _TOKEN_URL: str = ""
    _SCOPE_STR: str = ""
    _CLIENT_ID_ATTR: str = ""
    _CLIENT_SECRET_ATTR: str = ""
    _REDIRECT_SERVICE: str = ""

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params: dict = {
            "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
            "redirect_uri": REDIRECT_URI.format(service=self._REDIRECT_SERVICE),
            "response_type": "code",
            "state": state,
        }
        if self._SCOPE_STR:
            params["scope"] = self._SCOPE_STR
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return f"{self._AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        data: dict = {
            "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
            "client_secret": getattr(settings, self._CLIENT_SECRET_ATTR, "") or "",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI.format(service=self._REDIRECT_SERVICE),
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        async with httpx.AsyncClient() as client:
            response = await client.post(self._TOKEN_URL, data=data)
        body = response.json()
        if "error" in body:
            raise ValueError(
                f"{self.name} OAuth failed: {body.get('error_description', body['error'])}"
            )
        return with_expiry_metadata(body)

    async def refresh_access_token(self, refresh_token: str):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._TOKEN_URL,
                data={
                    "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
                    "client_secret": getattr(settings, self._CLIENT_SECRET_ATTR, "") or "",
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
        body = response.json()
        if "access_token" not in body:
            err = body.get("error_description") or body.get("error") or body
            raise ValueError(f"{self.name} token refresh failed: {err}")
        return with_expiry_metadata(body)
