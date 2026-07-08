"""API-key credential provider for mothership.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mothership_api_key",
    name="Mothership",
    icon_slug="mothership",
    color="#ffffff",
    description="Mothership — freight shipment quoting and booking.",
    hint="Mothership API key",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Mothership API key"
        ),
    ],
)
