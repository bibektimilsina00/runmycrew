"""API-key credential provider for intercom.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="intercom_api_key",
    name="Intercom",
    icon_slug="intercom",
    color="#ffffff",
    description="Intercom — contacts, conversations, messages.",
    hint="Access token (Developer Hub → Authentication)",
    fields=[
        CredentialField(id="api_key", label="Access Token", type="password", placeholder="Token")
    ],
)
