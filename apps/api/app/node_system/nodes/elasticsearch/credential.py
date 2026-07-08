"""API-key credential provider for elasticsearch.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="elasticsearch_api_key",
    name="Elasticsearch",
    icon_slug="elasticsearch",
    color="#ffffff",
    description="Elasticsearch — index, search, aggregate documents.",
    hint="Elasticsearch credentials",
    fields=[
        CredentialField(id="username", label="Username", type="string", placeholder="elastic"),
        CredentialField(
            id="api_key", label="Password / API Key", type="password", placeholder="Password"
        ),
        CredentialField(
            id="host",
            label="Host",
            type="string",
            placeholder="https://xxx.es.us-east-1.aws.elastic.cloud",
        ),
    ],
)
