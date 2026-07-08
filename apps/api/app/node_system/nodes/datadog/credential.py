"""API-key credential provider for datadog.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="datadog_api_key",
    name="Datadog",
    icon_slug="datadog",
    color="#ffffff",
    description="Datadog — metrics, logs, events, monitors.",
    hint="From Datadog settings",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Datadog API key"
        ),
        CredentialField(
            id="app_key",
            label="Application Key",
            type="password",
            placeholder="Datadog application key",
        ),
    ],
)
