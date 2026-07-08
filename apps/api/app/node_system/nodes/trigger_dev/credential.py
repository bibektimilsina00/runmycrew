"""API-key credential provider for trigger_dev.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="trigger_dev_api_key",
    name="Trigger.dev",
    icon_slug="trigger_dev",
    color="#ffffff",
    description="Trigger.dev — trigger background job runs, inspect runs.",
    hint="Trigger.dev API key",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Trigger.dev API key"
        ),
    ],
)
