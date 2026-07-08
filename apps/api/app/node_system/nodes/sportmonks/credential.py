"""API-key credential provider for sportmonks.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="sportmonks_api_key",
    name="SportMonks",
    icon_slug="sportmonks",
    color="#ffffff",
    description="SportMonks — football (soccer) live scores, fixtures, leagues.",
    hint="SportMonks API key",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="SportMonks API key"
        ),
    ],
)
