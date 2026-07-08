"""API-key credential provider for tinybird.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="tinybird_api_key",
    name="Tinybird",
    icon_slug="tinybird",
    color="#ffffff",
    description="Tinybird — managed ClickHouse for product analytics.",
    hint="Workspace admin or pipe token",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="p.eyJ...")
    ],
)
