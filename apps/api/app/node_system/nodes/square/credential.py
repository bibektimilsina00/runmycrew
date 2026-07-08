"""API-key credential provider for square.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="square_api_key",
    name="Square",
    icon_slug="square",
    color="#ffffff",
    description="Square Connect — payments, orders, customers, catalog.",
    hint="Access Token",
    fields=[
        CredentialField(id="api_key", label="Access Token", type="password", placeholder="EAAA...")
    ],
)
