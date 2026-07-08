"""API-key credential provider for luma.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="luma_api_key",
    name="Luma",
    icon_slug="luma",
    color="#ffffff",
    description="Luma — events + calendars via lu.ma.",
    hint="API key from Luma",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="Luma API key"),
    ],
)
