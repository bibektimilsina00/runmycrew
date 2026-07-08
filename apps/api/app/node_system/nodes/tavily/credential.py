"""API-key credential provider for tavily.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="tavily_api_key",
    name="Tavily",
    icon_slug="tavily",
    color="#ffffff",
    description="Tavily — LLM-grounded search + URL extraction.",
    hint="tvly-...",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="tvly-...")
    ],
)
