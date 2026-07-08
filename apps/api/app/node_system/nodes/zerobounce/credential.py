"""API-key credential provider for zerobounce.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="zerobounce_api_key",
    name="ZeroBounce",
    icon_slug="zerobounce",
    color="#ffffff",
    description="ZeroBounce — email verification + activity data.",
    hint="API key from ZeroBounce dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="ZeroBounce API key"
        ),
    ],
)
