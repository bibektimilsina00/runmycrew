from __future__ import annotations

from apps.api.app.credential_manager.oauth.base import (
    _SimpleOAuthProvider,
)


class AsanaOAuthProvider(_SimpleOAuthProvider):
    id = "asana_oauth"
    name = "Asana"
    icon_slug = "asana"
    color = "#1c1c1c"
    description = "Connect Asana for projects, tasks, and team workflows."
    scopes = [
        "Read and write tasks, projects, sections, and comments",
        "Read your workspace and team metadata",
    ]
    _AUTH_URL = "https://app.asana.com/-/oauth_authorize"
    _TOKEN_URL = "https://app.asana.com/-/oauth_token"
    _SCOPE_STR = "default"
    _CLIENT_ID_ATTR = "ASANA_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "ASANA_CLIENT_SECRET"
    _REDIRECT_SERVICE = "asana"


PROVIDER = AsanaOAuthProvider()
