"""API-key credential provider for agiloft.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="agiloft_api_key",
    name="Agiloft",
    icon_slug="agiloft",
    color="#ffffff",
    description="Agiloft — contract lifecycle management (CLM) records.",
    hint="Agiloft API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Agiloft API key"
        ),
    ],
)
