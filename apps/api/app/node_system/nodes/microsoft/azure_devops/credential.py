"""API-key credential provider for azure_devops.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="azure_devops_api_key",
    name="Azure DevOps",
    icon_slug="azure_devops",
    color="#ffffff",
    description="Azure DevOps — Personal Access Token (PAT).",
    hint="PAT from Azure DevOps → User Settings → Personal Access Tokens",
    fields=[
        CredentialField(
            id="api_key", label="Personal Access Token", type="password", placeholder="pat_..."
        ),
        CredentialField(
            id="organization", label="Organization", type="string", placeholder="my-org"
        ),
        CredentialField(id="project", label="Project", type="string", placeholder="my-project"),
    ],
)
