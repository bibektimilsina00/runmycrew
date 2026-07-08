"""API-key credential provider for ashby.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="ashby_api_key",
    name="Ashby",
    icon_slug="ashby",
    color="#ffffff",
    description="Ashby ATS — candidates, applications, jobs via POST-based JSON API.",
    hint="API key from Admin → API keys",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="ashby_v1_...",
        ),
    ],
)
