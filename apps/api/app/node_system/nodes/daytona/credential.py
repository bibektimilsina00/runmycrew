"""API-key credential provider for daytona.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="daytona_api_key",
    name="Daytona",
    icon_slug="daytona",
    color="#ffffff",
    description="Daytona — cloud dev environments.",
    hint="Daytona API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Daytona API key"
        ),
    ],
)
