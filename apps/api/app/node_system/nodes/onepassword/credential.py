"""API-key credential provider for onepassword.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="onepassword_api_key",
    name="1Password Connect",
    icon_slug="onepassword",
    color="#1c1c1c",
    description="1Password — fetch secrets from a vault via Connect API.",
    hint="1Password Connect API access",
    fields=[
        CredentialField(
            id="api_key",
            label="Connect Token",
            type="password",
            placeholder="1Password Connect token",
        ),
        CredentialField(
            id="host",
            label="Connect Host",
            type="string",
            placeholder="https://connect.example.com",
        ),
    ],
)
