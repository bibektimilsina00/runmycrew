"""API-key credential provider for profound.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="profound_api_key",
    name="Profound",
    icon_slug="profound",
    color="#ffffff",
    description="Profound — AI-answer / share-of-voice analytics.",
    hint="Profound API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Profound API key"
        ),
    ],
)
