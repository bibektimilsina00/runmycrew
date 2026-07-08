"""API-key credential provider for discord_bot_token.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="discord_bot_token",
    name="Discord Bot Token",
    icon_slug="discord",
    color="#ffffff",
    description="Discord — bot token for the Discord action node.",
    hint="Bot token from Discord Developer Portal",
    fields=[
        CredentialField(id="api_key", label="Bot Token", type="password", placeholder="MTA..."),
    ],
)
