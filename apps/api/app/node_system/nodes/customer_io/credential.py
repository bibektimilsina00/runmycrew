"""API-key credential provider for customer_io.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="customer_io_api_key",
    name="Customer.io",
    icon_slug="customer-io",
    color="#ffffff",
    description="Customer.io — behavioral messaging + broadcasts.",
    hint="Track site ID + track API key",
    fields=[
        CredentialField(
            id="site_id",
            label="Site ID",
            type="string",
            placeholder="Site ID",
        ),
        CredentialField(
            id="api_key",
            label="Track API Key",
            type="password",
            placeholder="Track API Key",
        ),
    ],
)
