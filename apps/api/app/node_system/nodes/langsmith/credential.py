"""API-key credential provider for langsmith.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="langsmith_api_key",
    name="LangSmith",
    icon_slug="langsmith",
    color="#ffffff",
    description="LangSmith — LLM trace + evaluation platform.",
    hint="From LangSmith settings",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="LangSmith API key"
        ),
    ],
)
