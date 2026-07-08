"""API-key credential provider for slack_bot_token.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="slack_bot_token",
    name="Slack Bot Token",
    icon_slug="slack",
    color="#ffffff",
    description="Slack — direct bot token (xoxb-...) alternative to OAuth.",
    hint="From Slack app → OAuth & Permissions",
    fields=[
        CredentialField(id="api_key", label="Bot Token", type="password", placeholder="xoxb-..."),
    ],
)
