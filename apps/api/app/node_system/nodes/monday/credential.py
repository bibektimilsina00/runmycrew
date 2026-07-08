"""API-key credential provider for monday.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="monday_api_key",
    name="Monday.com",
    icon_slug="monday",
    color="#ffffff",
    description="Monday.com — boards, items, updates via GraphQL.",
    hint="API token (Profile → Admin → API)",
    fields=[CredentialField(id="api_key", label="API Token", type="password", placeholder="Token")],
)
