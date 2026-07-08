"""API-key credential provider for cursor.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="cursor_api_key",
    name="Cursor",
    icon_slug="cursor",
    color="#ffffff",
    description="Cursor — AI code editor. Background agents API.",
    hint="API key from Cursor dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Cursor API key"
        ),
    ],
)
