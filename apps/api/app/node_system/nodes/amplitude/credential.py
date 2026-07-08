"""API-key credential provider for amplitude.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="amplitude_api_key",
    name="Amplitude",
    icon_slug="amplitude",
    color="#ffffff",
    description="Amplitude — product analytics event ingestion.",
    hint="From Amplitude settings",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Amplitude API key"
        ),
        CredentialField(
            id="secret_key",
            label="Secret Key (for chart export, placeholder=)",
            type="password",
            placeholder="Amplitude secret key",
        ),
    ],
)
