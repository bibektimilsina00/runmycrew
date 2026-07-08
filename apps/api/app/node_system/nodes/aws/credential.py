"""API-key credential provider for aws.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="aws_credentials",
    name="AWS",
    icon_slug="aws",
    color="#1c1c1c",
    description=(
        "AWS access key + secret access key. Signs SigV4 requests "
        "for S3, SES, SQS, Secrets Manager, Athena, and other AWS APIs."
    ),
    hint="Access Key ID + Secret Access Key + Region",
    fields=[
        CredentialField(
            id="access_key_id",
            label="Access Key ID",
            type="string",
            placeholder="AKIA...",
        ),
        CredentialField(
            id="secret_access_key",
            label="Secret Access Key",
            type="password",
            placeholder="secret",
        ),
        CredentialField(
            id="region",
            label="Default Region",
            type="string",
            placeholder="us-east-1",
        ),
        CredentialField(
            id="session_token",
            label="Session Token (optional, STS, placeholder=)",
            type="password",
            placeholder="STS token",
        ),
    ],
)
