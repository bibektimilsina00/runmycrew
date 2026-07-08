"""API-key credential provider for telegram_bot.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="telegram_bot",
    name="Telegram Bot",
    icon_slug="telegram",
    color="#ffffff",
    description="Telegram bot token (from @BotFather). Used for send_message + getUpdates polling.",
    hint="Bot token in the form 123456:ABC-DEF...",
    fields=[
        CredentialField(
            id="bot_token",
            label="Bot Token",
            type="password",
            placeholder="123456789:ABCDEF...",
        ),
    ],
)
