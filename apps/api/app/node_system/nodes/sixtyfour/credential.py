"""API-key credential provider for sixtyfour.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="sixtyfour_api_key",
    name="SixtyFour",
    icon_slug="sixtyfour",
    color="#ffffff",
    description="SixtyFour — AI research for lead enrichment.",
    hint="API key from SixtyFour dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="SixtyFour API key"
        ),
    ],
)
