"""API-key credential provider for greenhouse.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="greenhouse_api_key",
    name="Greenhouse",
    icon_slug="greenhouse",
    color="#ffffff",
    description="Greenhouse ATS — jobs, candidates, applications via Harvest API v1.",
    hint="Harvest API key (Basic auth as user, no password)",
    fields=[
        CredentialField(
            id="api_key",
            label="Harvest API Key",
            type="password",
            placeholder="Harvest key from Greenhouse settings",
        ),
    ],
)
