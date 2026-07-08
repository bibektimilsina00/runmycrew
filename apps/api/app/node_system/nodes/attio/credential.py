"""API-key credential provider for attio.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="attio_api_key",
    name="Attio",
    icon_slug="attio",
    color="#ffffff",
    description="Attio CRM — flexible-schema records, lists, and objects.",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
