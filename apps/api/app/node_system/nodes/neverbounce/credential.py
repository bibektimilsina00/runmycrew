"""API-key credential provider for neverbounce.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="neverbounce_api_key",
    name="NeverBounce",
    icon_slug="neverbounce",
    color="#ffffff",
    description="NeverBounce — real-time email verification.",
    hint="API key from NeverBounce dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="NeverBounce API key"
        ),
    ],
)
