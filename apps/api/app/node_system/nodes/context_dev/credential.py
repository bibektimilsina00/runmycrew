"""API-key credential provider for context_dev.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="context_dev_api_key",
    name="Context",
    icon_slug="context_dev",
    color="#ffffff",
    description="Context — LLM answer analytics + user feedback.",
    hint="API key from Context dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Context API key"
        ),
    ],
)
