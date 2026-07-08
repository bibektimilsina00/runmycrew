"""API-key credential provider for jina.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="jina_api_key",
    name="Jina AI",
    icon_slug="jina",
    color="#ffffff",
    description="Jina — search, reader, embed via jina.ai.",
    hint="API key from Jina AI dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Jina AI API key"
        ),
    ],
)
