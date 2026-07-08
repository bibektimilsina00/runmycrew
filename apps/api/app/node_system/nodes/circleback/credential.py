"""API-key credential provider for circleback.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="circleback_api_key",
    name="Circleback",
    icon_slug="circleback",
    color="#ffffff",
    description="Circleback — AI meeting notes + action items.",
    hint="API key from Circleback",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Circleback API key"
        ),
    ],
)
