"""API-key credential provider for parallel_ai.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="parallel_ai_api_key",
    name="Parallel AI",
    icon_slug="parallel_ai",
    color="#ffffff",
    description="Parallel AI — web-scale research / task API.",
    hint="Parallel AI API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Parallel AI API key"
        ),
    ],
)
