"""API-key credential provider for notion.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="notion_api_key",
    name="Notion",
    icon_slug="notion",
    color="#1c1c1c",
    description="Connect to Notion using an Internal Integration Token",
    hint="secret_...",
    fields=[
        CredentialField(
            id="api_key",
            label="Integration Token",
            type="password",
            placeholder="secret_...",
        )
    ],
)
