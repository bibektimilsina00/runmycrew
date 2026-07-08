"""API-key credential provider for sap_concur.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="sap_concur_api_key",
    name="SAP Concur",
    icon_slug="sap_concur",
    color="#ffffff",
    description="SAP Concur — travel + expense management.",
    hint="SAP Concur API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="SAP Concur API key"
        ),
    ],
)
