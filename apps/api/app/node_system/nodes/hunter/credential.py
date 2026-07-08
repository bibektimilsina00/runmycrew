"""API-key credential provider for hunter.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="hunter_api_key",
    name="Hunter.io",
    icon_slug="hunter",
    color="#ffffff",
    description="Hunter — email finder + verifier by domain.",
    hint="API key from Hunter Dashboard → API",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Hunter API key"
        ),
    ],
)
