"""API-key credential provider for quartr.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="quartr_api_key",
    name="Quartr",
    icon_slug="quartr",
    color="#ffffff",
    description="Quartr — earnings-call transcripts + investor events.",
    hint="Quartr API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Quartr API key"
        ),
    ],
)
