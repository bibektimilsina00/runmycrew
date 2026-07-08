"""API-key credential provider for qdrant.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="qdrant_api_key",
    name="Qdrant",
    icon_slug="qdrant",
    color="#ffffff",
    description="Qdrant — vector database (cloud or self-hosted).",
    hint="Cluster URL + API key",
    fields=[
        CredentialField(
            id="cluster_url",
            label="Cluster URL",
            type="string",
            placeholder="https://abc.us-east.aws.cloud.qdrant.io:6333",
        ),
        CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key"),
    ],
)
