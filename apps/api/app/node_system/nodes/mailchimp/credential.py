"""API-key credential provider for mailchimp.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mailchimp_api_key",
    name="Mailchimp",
    icon_slug="mailchimp",
    color="#ffffff",
    description="Mailchimp — audiences, campaigns, transactional.",
    hint="API Key (ends in -us14) + data-center suffix from the key",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="abc123-us14",
        ),
        CredentialField(
            id="dc",
            label="Data Center",
            type="string",
            placeholder="us14 (the suffix after the dash in your API key)",
        ),
    ],
)
