"""API-key credential provider for millionverifier.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="millionverifier_api_key",
    name="MillionVerifier",
    icon_slug="millionverifier",
    color="#ffffff",
    description="MillionVerifier — email + phone verification.",
    hint="API key from MillionVerifier dashboard",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="MillionVerifier API key",
        ),
    ],
)
