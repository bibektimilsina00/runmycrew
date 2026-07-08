"""API-key credential provider for databricks.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="databricks_api_key",
    name="Databricks",
    icon_slug="databricks",
    color="#ffffff",
    description="Databricks — SQL warehouses, jobs, notebooks.",
    hint="Databricks credentials",
    fields=[
        CredentialField(
            id="api_key", label="Personal Access Token", type="password", placeholder="dapi..."
        ),
        CredentialField(
            id="workspace_url",
            label="Workspace URL",
            type="string",
            placeholder="https://dbc-xxx.cloud.databricks.com",
        ),
    ],
)
