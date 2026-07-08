from __future__ import annotations

from apps.api.app.credential_manager.oauth.base import (
    _SimpleOAuthProvider,
)


class CalendlyOAuthProvider(_SimpleOAuthProvider):
    id = "calendly_oauth"
    name = "Calendly"
    icon_slug = "calendly"
    color = "#1c1c1c"
    description = "Connect Calendly for scheduled events, invitees, and webhooks."
    scopes = [
        "Read your scheduled events and invitee details",
        "Manage webhook subscriptions for new bookings",
        "Read your Calendly user profile",
    ]
    _AUTH_URL = "https://auth.calendly.com/oauth/authorize"
    _TOKEN_URL = "https://auth.calendly.com/oauth/token"
    _SCOPE_STR = "default"
    _CLIENT_ID_ATTR = "CALENDLY_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "CALENDLY_CLIENT_SECRET"
    _REDIRECT_SERVICE = "calendly"


PROVIDER = CalendlyOAuthProvider()
