"""API-key credential provider for kalshi.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="kalshi_api_key",
    name="Kalshi",
    icon_slug="kalshi",
    color="#ffffff",
    description="Kalshi — prediction market events, markets, orders.",
    hint="Kalshi API key",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Kalshi API key"
        ),
    ],
)
