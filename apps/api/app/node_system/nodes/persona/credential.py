"""API-key credential provider for persona.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="persona_api_key",
    name="Persona",
    icon_slug="persona",
    color="#ffffff",
    description="Persona — identity verification + KYC.",
    hint="API key from Persona dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Persona API key"
        ),
    ],
)
