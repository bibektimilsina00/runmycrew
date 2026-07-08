"""API-key credential provider for fathom.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="fathom_api_key",
    name="Fathom",
    icon_slug="fathom",
    color="#ffffff",
    description="Fathom.video — meeting recordings, transcripts, action items.",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
