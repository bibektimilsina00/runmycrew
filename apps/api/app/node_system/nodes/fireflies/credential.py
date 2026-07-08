"""API-key credential provider for fireflies.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="fireflies_api_key",
    name="Fireflies",
    icon_slug="fireflies",
    color="#ffffff",
    description="Fireflies.ai — meeting transcripts + summaries + search (GraphQL).",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
