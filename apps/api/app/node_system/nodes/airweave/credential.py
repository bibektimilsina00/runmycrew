"""API-key credential provider for airweave.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="airweave_api_key",
    name="Airweave",
    icon_slug="airweave",
    color="#ffffff",
    description="Airweave — RAG data pipeline sync sources → destinations.",
    hint="Airweave API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Airweave API key"
        ),
    ],
)
