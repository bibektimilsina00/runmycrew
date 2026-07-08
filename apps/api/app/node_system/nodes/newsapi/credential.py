"""API-key credential provider for newsapi.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="newsapi_api_key",
    name="NewsAPI",
    icon_slug="newsapi",
    color="#ffffff",
    description="NewsAPI.org — search 80k+ news sources.",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
