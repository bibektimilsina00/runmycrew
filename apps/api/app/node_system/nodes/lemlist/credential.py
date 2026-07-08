"""API-key credential provider for lemlist.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="lemlist_api_key",
    name="Lemlist",
    icon_slug="lemlist",
    color="#ffffff",
    description="Lemlist — outbound email campaigns, leads, activities.",
    hint="API key from Lemlist Settings → API",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Lemlist API key",
        ),
    ],
)
