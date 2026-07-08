"""API-key credential provider for apify.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="apify_api_key",
    name="Apify",
    icon_slug="apify",
    color="#ffffff",
    description="Apify — actors, datasets, key-value stores.",
    hint="Personal API token",
    fields=[
        CredentialField(
            id="api_key", label="API Token", type="password", placeholder="apify_api_..."
        )
    ],
)
