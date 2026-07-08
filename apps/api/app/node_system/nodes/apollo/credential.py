"""API-key credential provider for apollo.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="apollo_api_key",
    name="Apollo.io",
    icon_slug="apollo",
    color="#ffffff",
    description="Apollo — B2B contact search + email finder.",
    hint="API key from Apollo Settings → Integrations → API",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Apollo API key"
        ),
    ],
)
