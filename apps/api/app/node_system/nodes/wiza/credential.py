"""API-key credential provider for wiza.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="wiza_api_key",
    name="Wiza",
    icon_slug="wiza",
    color="#1c1c1c",
    description="Wiza — LinkedIn scraper + email enrichment.",
    hint="API key from Wiza dashboard",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="Wiza API key"),
    ],
)
