"""API-key credential provider for mem0.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mem0_api_key",
    name="Mem0",
    icon_slug="mem0",
    color="#ffffff",
    description="Mem0 — persistent memory for AI agents.",
    hint="Mem0 API access",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="Mem0 API key"),
    ],
)
