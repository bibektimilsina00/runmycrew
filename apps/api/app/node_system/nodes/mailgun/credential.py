"""API-key credential provider for mailgun.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mailgun_api_key",
    name="Mailgun",
    icon_slug="mailgun",
    color="#ffffff",
    description="Mailgun — transactional + marketing email.",
    hint="key-... (private API key)",
    fields=[
        CredentialField(
            id="api_key", label="Private API Key", type="password", placeholder="key-..."
        )
    ],
)
