"""API-key credential provider for gamma.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="gamma_api_key",
    name="Gamma",
    icon_slug="gamma",
    color="#ffffff",
    description="Gamma — AI-generated presentations, docs, sites.",
    hint="Gamma API access",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key / Bearer Token",
            type="password",
            placeholder="Gamma API key",
        ),
    ],
)
