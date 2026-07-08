"""API-key credential provider for linkup.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="linkup_api_key",
    name="Linkup",
    icon_slug="linkup",
    color="#ffffff",
    description="Linkup — real-time web search (better recall than SerpAPI).",
    hint="Linkup API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Linkup API key"
        ),
    ],
)
