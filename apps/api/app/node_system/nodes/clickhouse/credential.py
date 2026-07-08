"""API-key credential provider for clickhouse.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="clickhouse_api_key",
    name="ClickHouse Cloud",
    icon_slug="clickhouse",
    color="#ffffff",
    description="ClickHouse Cloud — analytics DB via HTTP interface.",
    hint="ClickHouse Cloud credentials",
    fields=[
        CredentialField(id="username", label="Username", type="string", placeholder="default"),
        CredentialField(id="api_key", label="Password", type="password", placeholder="Password"),
        CredentialField(
            id="host", label="Host", type="string", placeholder="https://xxx.clickhouse.cloud"
        ),
    ],
)
