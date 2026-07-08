"""API-key credential provider for rippling.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="rippling_api_key",
    name="Rippling",
    icon_slug="rippling",
    color="#ffffff",
    description="Rippling — HR platform (employees, orgs, payroll).",
    hint="Rippling API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Rippling API key"
        ),
    ],
)
