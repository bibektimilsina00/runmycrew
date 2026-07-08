"""API-key credential provider for google_search.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="google_search_api_key",
    name="Google Search",
    icon_slug="google_search",
    color="#4285F4",
    description="Google Custom Search JSON API — indexed web + image results.",
    hint="Google Search API access",
    fields=[
        CredentialField(
            id="api_key", label="Google Cloud API Key", type="password", placeholder="AIzaSy..."
        ),
    ],
)
