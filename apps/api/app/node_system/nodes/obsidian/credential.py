"""API-key credential provider for obsidian.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="obsidian_api_key",
    name="Obsidian Local REST",
    icon_slug="obsidian",
    color="#ffffff",
    description="Obsidian Local REST plugin — vault notes CRUD.",
    hint="Obsidian Local REST API access",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Obsidian Local REST API key",
        ),
    ],
)
