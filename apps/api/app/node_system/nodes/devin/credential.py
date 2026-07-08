"""API-key credential provider for devin.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="devin_api_key",
    name="Devin",
    icon_slug="devin",
    color="#ffffff",
    description="Devin — Cognition AI software engineer agent.",
    hint="API key from Devin dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Devin API key"
        ),
    ],
)
