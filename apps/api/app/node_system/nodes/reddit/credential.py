"""API-key credential provider for reddit.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="reddit_api_key",
    name="Reddit",
    icon_slug="reddit",
    color="#ffffff",
    description="Reddit — subreddit browsing, submissions, comments.",
    hint="Reddit API access",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key / Bearer Token",
            type="password",
            placeholder="Reddit API key",
        ),
    ],
)
