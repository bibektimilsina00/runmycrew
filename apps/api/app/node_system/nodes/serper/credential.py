"""API-key credential provider for serper.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="serper_api_key",
    name="Serper",
    icon_slug="serper",
    color="#ffffff",
    description="Serper — Google search results via google.serper.dev.",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
