"""API-key credential provider for brex.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="brex_api_key",
    name="Brex",
    icon_slug="brex",
    color="#ffffff",
    description="Brex — corporate cards + expense management.",
    hint="Brex API access",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="Brex API key"),
    ],
)
