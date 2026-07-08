"""API-key credential provider for linear.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="linear_api_key",
    name="Linear",
    icon_slug="linear",
    color="#ffffff",
    description="Linear project management — create and manage issues",
    hint="lin_api_...",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="lin_api_...")
    ],
)
