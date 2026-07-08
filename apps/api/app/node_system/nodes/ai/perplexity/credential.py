"""API-key credential provider for perplexity.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="perplexity_api_key",
    name="Perplexity",
    icon_slug="perplexity",
    color="#ffffff",
    description="Perplexity Sonar — web search + LLM with live internet access",
    hint="pplx-...",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="pplx-...")
    ],
)
