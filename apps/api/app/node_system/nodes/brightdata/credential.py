"""API-key credential provider for brightdata.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="brightdata_api_key",
    name="Bright Data",
    icon_slug="brightdata",
    color="#ffffff",
    description="Bright Data — proxy + web scraping API.",
    hint="API key from Bright Data dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Bright Data API key"
        ),
    ],
)
