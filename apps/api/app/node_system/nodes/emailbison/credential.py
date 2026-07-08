"""API-key credential provider for emailbison.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="emailbison_api_key",
    name="Emailbison",
    icon_slug="emailbison",
    color="#ffffff",
    description="Emailbison — outbound-email campaigns, leads, workspaces.",
    hint="API key from Emailbison workspace settings",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Emailbison API key",
        ),
    ],
)
