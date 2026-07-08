"""API-key credential provider for wealthbox.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="wealthbox_api_key",
    name="Wealthbox",
    icon_slug="wealthbox",
    color="#ffffff",
    description="Wealthbox — CRM for financial advisors.",
    hint="Wealthbox API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Wealthbox API key"
        ),
    ],
)
