"""API-key credential provider for enrichment.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="enrichment_api_key",
    name="Enrichment.io",
    icon_slug="enrichment",
    color="#ffffff",
    description="Enrichment — contact + company data-as-a-service.",
    hint="API key from Enrichment.io dashboard",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Enrichment.io API key",
        ),
    ],
)
