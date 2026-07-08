"""API-key credential provider for vanta.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="vanta_api_key",
    name="Vanta",
    icon_slug="vanta",
    color="#ffffff",
    description="Vanta — compliance controls, findings, security tests.",
    hint="Vanta API key",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Vanta API key"
        ),
    ],
)
