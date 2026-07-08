"""API-key credential provider for rb2b.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="rb2b_api_key",
    name="RB2B",
    icon_slug="rb2b",
    color="#1c1c1c",
    description="RB2B — identify anonymous website visitors (B2B).",
    hint="RB2B API access",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="RB2B API key"),
    ],
)
