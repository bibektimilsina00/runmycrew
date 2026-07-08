"""API-key credential provider for extend.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="extend_api_key",
    name="Extend",
    icon_slug="extend",
    color="#ffffff",
    description="Extend — document extraction (invoices, receipts, PDFs).",
    hint="API key from Extend",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Extend API key"
        ),
    ],
)
