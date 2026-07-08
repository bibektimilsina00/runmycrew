"""API-key credential provider for okta.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="okta_api_key",
    name="Okta",
    icon_slug="okta",
    color="#ffffff",
    description="Okta — identity users, groups, apps, MFA.",
    hint="Okta API access",
    fields=[
        CredentialField(
            id="api_key",
            label="Okta API Token (prefix with SSWS , placeholder=)",
            type="password",
            placeholder="SSWS 00xxx...",
        ),
        CredentialField(
            id="domain", label="Okta Domain", type="string", placeholder="mycompany.okta.com"
        ),
    ],
)
