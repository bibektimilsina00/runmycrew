"""API-key credential provider for brandfetch.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="brandfetch_api_key",
    name="Brandfetch",
    icon_slug="brandfetch",
    color="#ffffff",
    description="Brandfetch — pull brand identity assets by domain.",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
