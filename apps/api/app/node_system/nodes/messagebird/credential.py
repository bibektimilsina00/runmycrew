"""API-key credential provider for messagebird.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="messagebird_api_key",
    name="MessageBird",
    icon_slug="messagebird",
    color="#ffffff",
    description="MessageBird — SMS, voice, verification.",
    hint="Access Key",
    fields=[
        CredentialField(id="api_key", label="Access Key", type="password", placeholder="Access Key")
    ],
)
