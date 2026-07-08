"""API-key credential provider for gitlab.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="gitlab_api_key",
    name="GitLab",
    icon_slug="gitlab",
    color="#ffffff",
    description="GitLab — projects, issues, MRs, pipelines.",
    hint="Personal Access Token",
    fields=[
        CredentialField(
            id="api_key", label="Access Token", type="password", placeholder="glpat-..."
        ),
        CredentialField(
            id="base_url",
            label="Base URL (self-hosted; leave blank for gitlab.com, placeholder=)",
            type="string",
            placeholder="https://gitlab.example.com",
        ),
    ],
)
