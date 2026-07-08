"""API-key credential provider for guardrails.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="guardrails_api_key",
    name="Guardrails AI",
    icon_slug="guardrails",
    color="#ffffff",
    description="Guardrails AI — validate + repair LLM output against JSON schema.",
    hint="Guardrails AI API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Guardrails AI API key"
        ),
    ],
)
