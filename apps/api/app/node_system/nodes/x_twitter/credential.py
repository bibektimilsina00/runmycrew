"""API-key credential provider for x_twitter.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="x_twitter_api_key",
    name="X (Twitter)",
    icon_slug="twitter",
    color="#1c1c1c",
    description="X (formerly Twitter) — tweets, users, timelines via API v2.",
    hint="X (Twitter) API access",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key / Bearer Token",
            type="password",
            placeholder="X (Twitter) API key",
        ),
    ],
)
