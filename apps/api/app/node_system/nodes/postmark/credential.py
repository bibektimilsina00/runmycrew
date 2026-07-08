"""API-key credential provider for postmark.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="postmark_api_key",
    name="Postmark",
    icon_slug="postmark",
    color="#ffffff",
    description="Postmark — fast transactional email.",
    hint="Server Token (one per Postmark server)",
    fields=[
        CredentialField(
            id="api_key", label="Server Token", type="password", placeholder="Server Token"
        )
    ],
)
