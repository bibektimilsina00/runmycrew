"""API-key credential provider for enrich.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="enrich_api_key",
    name="Enrich.so",
    icon_slug="enrich",
    color="#ffffff",
    description="Enrich.so — LinkedIn scraper + email finder.",
    hint="API key from Enrich.so dashboard",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Enrich.so API key",
        ),
    ],
)
