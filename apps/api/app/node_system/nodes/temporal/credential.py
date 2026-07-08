"""API-key credential provider for temporal.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="temporal_api_key",
    name="Temporal Cloud",
    icon_slug="temporal",
    color="#ffffff",
    description="Temporal Cloud — workflow orchestration API.",
    hint="Temporal Cloud credentials",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Temporal Cloud API key"
        ),
    ],
)
