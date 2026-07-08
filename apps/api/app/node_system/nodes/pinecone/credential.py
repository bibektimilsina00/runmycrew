"""API-key credential provider for pinecone.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="pinecone_api_key",
    name="Pinecone",
    icon_slug="pinecone",
    color="#ffffff",
    description="Pinecone — vector database control + data plane.",
    hint="API key + per-index host",
    fields=[
        CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key"),
        CredentialField(
            id="index_host",
            label="Index Host (optional, data-plane ops, placeholder=)",
            type="string",
            placeholder="abc-123456.svc.us-east-1.aws.pinecone.io",
        ),
    ],
)
