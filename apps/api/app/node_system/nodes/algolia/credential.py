"""API-key credential provider for algolia.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="algolia_api_key",
    name="Algolia",
    icon_slug="algolia",
    color="#ffffff",
    description="Algolia — index, search, manage records.",
    hint="Application ID + Admin / Search API key",
    fields=[
        CredentialField(
            id="app_id",
            label="Application ID",
            type="string",
            placeholder="ABC123",
        ),
        CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key"),
    ],
)
