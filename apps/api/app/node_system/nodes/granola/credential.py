"""API-key credential provider for granola.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="granola_api_key",
    name="Granola",
    icon_slug="granola",
    color="#ffffff",
    description="Granola — AI meeting notes for Mac.",
    hint="API key from Granola",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Granola API key"
        ),
    ],
)
