"""API-key credential provider for clay.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="clay_api_key",
    name="Clay",
    icon_slug="clay",
    color="#ffffff",
    description="Clay — push rows into a workspace table for enrichment.",
    hint="Workspace webhook URL from a Clay table (paste as api_key)",
    fields=[
        CredentialField(
            id="webhook_url",
            label="Clay Workspace Webhook URL",
            type="string",
            placeholder="https://api.clay.com/v3/sources/webhook/...",
        ),
        CredentialField(
            id="api_key",
            label="Auth Token (optional; some workspaces require, placeholder=)",
            type="password",
            placeholder="Optional",
        ),
    ],
)
