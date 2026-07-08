"""API-key credential provider for datagma.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="datagma_api_key",
    name="Datagma",
    icon_slug="datagma",
    color="#ffffff",
    description="Datagma — French B2B contact + company enrichment.",
    hint="API key from Datagma dashboard",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Datagma API key",
        ),
    ],
)
