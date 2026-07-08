"""API-key credential provider for ahrefs.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="ahrefs_api_key",
    name="Ahrefs",
    icon_slug="ahrefs",
    color="#1c1c1c",
    description="Ahrefs — SEO + backlinks + keyword research.",
    hint="API key from Ahrefs dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Ahrefs API key"
        ),
    ],
)
