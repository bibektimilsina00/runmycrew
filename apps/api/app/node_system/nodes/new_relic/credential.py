"""API-key credential provider for new_relic.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="new_relic_api_key",
    name="New Relic",
    icon_slug="new_relic",
    color="#ffffff",
    description="New Relic — APM, logs, metrics via NRQL + events.",
    hint="From New Relic settings",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="New Relic API key"
        ),
    ],
)
