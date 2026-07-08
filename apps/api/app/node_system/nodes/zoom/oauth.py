from __future__ import annotations

from apps.api.app.credential_manager.oauth.base import (
    _SimpleOAuthProvider,
)


class ZoomOAuthProvider(_SimpleOAuthProvider):
    id = "zoom_oauth"
    name = "Zoom"
    icon_slug = "zoom"
    color = "#ffffff"
    description = "Connect Zoom for meeting management, users, and recordings."
    scopes = [
        "Read and write meetings on your account",
        "Read your Zoom user profile",
        "Read meeting recordings and transcripts",
    ]
    _AUTH_URL = "https://zoom.us/oauth/authorize"
    _TOKEN_URL = "https://zoom.us/oauth/token"
    _SCOPE_STR = "meeting:read meeting:write user:read recording:read"
    _CLIENT_ID_ATTR = "ZOOM_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "ZOOM_CLIENT_SECRET"
    _REDIRECT_SERVICE = "zoom"


PROVIDER = ZoomOAuthProvider()
