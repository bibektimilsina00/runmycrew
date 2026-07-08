"""API-key credential provider for infisical.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="infisical_api_key",
    name="Infisical",
    icon_slug="infisical",
    color="#ffffff",
    description="Infisical — secrets management (open-source Vault alt).",
    hint="Infisical API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Infisical API key"
        ),
    ],
)
