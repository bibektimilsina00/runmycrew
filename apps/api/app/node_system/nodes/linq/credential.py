"""API-key credential provider for linq.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="linq_api_key",
    name="LinQ",
    icon_slug="linq",
    color="#ffffff",
    description="LinQ — enterprise procurement + supplier data.",
    hint="LinQ API access",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="LinQ API key"),
    ],
)
