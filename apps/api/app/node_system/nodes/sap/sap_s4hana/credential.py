"""API-key credential provider for sap_s4hana.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="sap_s4hana_credentials",
    name="SAP S/4HANA Cloud",
    icon_slug="sap_s4hana",
    color="#ffffff",
    description="SAP S/4HANA Cloud — OData v2 business partners, sales orders, ledger.",
    hint="SAP S/4HANA Cloud API access",
    fields=[
        CredentialField(
            id="username", label="Username", type="string", placeholder="COMMUNICATION_USER"
        ),
        CredentialField(
            id="api_key", label="Password", type="password", placeholder="tenant password"
        ),
        CredentialField(
            id="host", label="Host", type="string", placeholder="my00000.s4hana.ondemand.com"
        ),
    ],
)
