"""API-key credential provider for grain.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="grain_api_key",
    name="Grain",
    icon_slug="grain",
    color="#ffffff",
    description="Grain — meeting recorder, highlights, stories via public API v3.",
    hint="Personal Access Token from Grain settings",
    fields=[
        CredentialField(
            id="api_key",
            label="Access Token",
            type="password",
            placeholder="grain_pat_...",
        ),
    ],
)
