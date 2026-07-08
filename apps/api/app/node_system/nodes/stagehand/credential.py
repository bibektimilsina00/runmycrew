"""API-key credential provider for stagehand.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="stagehand_api_key",
    name="Stagehand",
    icon_slug="stagehand",
    color="#ffffff",
    description="Stagehand — Browserbase AI browser automation.",
    hint="API key from Stagehand dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Stagehand API key"
        ),
    ],
)
