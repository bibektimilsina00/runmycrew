"""API-key credential provider for hubspot.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="hubspot_api_key",
    name="HubSpot",
    icon_slug="hubspot",
    color="#ffffff",
    description="HubSpot — CRM contacts, deals, and companies",
    hint="Private App Token",
    fields=[
        CredentialField(
            id="api_key", label="Private App Token", type="password", placeholder="pat-na1-..."
        )
    ],
)
