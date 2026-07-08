"""API-key credential provider for whatsapp.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="whatsapp_api_key",
    name="WhatsApp Business",
    icon_slug="whatsapp",
    color="#ffffff",
    description="WhatsApp Business Cloud API — send template + text messages.",
    hint="Meta Cloud API access token",
    fields=[
        CredentialField(id="api_key", label="Access Token", type="password", placeholder="EAAG..."),
    ],
)
