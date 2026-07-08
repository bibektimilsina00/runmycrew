"""API-key credential provider for google_books.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="google_books_api_key",
    name="Google Books",
    icon_slug="google_books",
    color="#ffffff",
    description="Google Books — search + fetch volume metadata.",
    hint="Google Books API key",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Google Books API key"
        ),
    ],
)
