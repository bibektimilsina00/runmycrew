"""API-key credential provider for gong.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="gong_api_key",
    name="Gong",
    icon_slug="gong",
    color="#ffffff",
    description="Gong.io — call recordings, transcripts, deal insights.",
    hint="Access Key + Access Key Secret",
    fields=[
        CredentialField(
            id="access_key",
            label="Access Key",
            type="string",
            placeholder="Access Key",
        ),
        CredentialField(
            id="access_key_secret",
            label="Access Key Secret",
            type="password",
            placeholder="Secret",
        ),
    ],
)
