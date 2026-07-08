"""API-key credential provider for calcom.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="calcom_api_key",
    name="Cal.com",
    icon_slug="calcom",
    color="#ffffff",
    description="Cal.com — bookings, event types, availability.",
    hint="cal_live_... (Cal.com API key)",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="cal_live_...")
    ],
)
