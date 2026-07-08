"""API-key credential provider for trello.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="trello_api_key",
    name="Trello",
    icon_slug="trello",
    color="#ffffff",
    description="Trello — boards, lists, cards. Uses API key + user token.",
    hint="API key (public) + Token (private per-user)",
    fields=[
        CredentialField(
            id="app_key",
            label="API Key",
            type="string",
            placeholder="from trello.com/app-key",
        ),
        CredentialField(
            id="api_key",
            label="User Token",
            type="password",
            placeholder="Manual token or OAuth1 accessToken",
        ),
    ],
)
