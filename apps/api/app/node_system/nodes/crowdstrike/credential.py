"""API-key credential provider for crowdstrike.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="crowdstrike_api_key",
    name="CrowdStrike Falcon",
    icon_slug="crowdstrike",
    color="#ffffff",
    description="CrowdStrike Falcon — hosts, detects, incidents.",
    hint="CrowdStrike Falcon API access",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="CrowdStrike Falcon API key",
        ),
    ],
)
