"""API-key credential provider for pulse.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="pulse_api_key",
    name="Pulse",
    icon_slug="pulse",
    color="#ffffff",
    description="Pulse — document parsing (PDF → structured JSON/markdown).",
    hint="Pulse API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Pulse API key"
        ),
    ],
)
