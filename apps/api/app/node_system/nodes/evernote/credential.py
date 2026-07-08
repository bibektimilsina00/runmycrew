"""API-key credential provider for evernote.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="evernote_api_key",
    name="Evernote",
    icon_slug="evernote",
    color="#ffffff",
    description="Evernote — notes, notebooks, tags.",
    hint="API key from Evernote",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Evernote API key"
        ),
    ],
)
