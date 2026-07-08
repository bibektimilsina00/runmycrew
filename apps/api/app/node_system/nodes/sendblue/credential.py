"""API-key credential provider for sendblue.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="sendblue_api_key",
    name="Sendblue",
    icon_slug="sendblue",
    color="#ffffff",
    description="Sendblue — iMessage + SMS fallback messaging.",
    hint="API Key ID + Secret",
    fields=[
        CredentialField(
            id="api_key_id",
            label="API Key ID",
            type="string",
            placeholder="key id",
        ),
        CredentialField(
            id="api_secret_key",
            label="API Secret Key",
            type="password",
            placeholder="secret key",
        ),
    ],
)
