"""API-key credential provider for zoominfo.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="zoominfo_api_key",
    name="ZoomInfo",
    icon_slug="zoominfo",
    color="#ffffff",
    description="ZoomInfo — B2B contact + company database.",
    hint="API key from ZoomInfo dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="ZoomInfo API key"
        ),
    ],
)
