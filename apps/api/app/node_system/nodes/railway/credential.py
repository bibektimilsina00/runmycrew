"""API-key credential provider for railway.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="railway_api_key",
    name="Railway",
    icon_slug="railway",
    color="#1c1c1c",
    description="Railway — deploy + manage services.",
    hint="Railway API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Railway API key"
        ),
    ],
)
