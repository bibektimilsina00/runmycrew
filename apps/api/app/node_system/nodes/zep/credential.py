"""API-key credential provider for zep.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="zep_api_key",
    name="Zep",
    icon_slug="zep",
    color="#ffffff",
    description="Zep — long-term memory + session tracking for AI apps.",
    hint="Zep API access",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="Zep API key"),
    ],
)
