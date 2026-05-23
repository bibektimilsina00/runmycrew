from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.credentials.manager.oauth.flow import get_oauth_provider
from apps.api.app.features.credentials.service import CredentialService
from apps.api.app.features.logs.service import LogsService
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace


async def handle_oauth_callback(
    service_name: str,
    code: str,
    user: User,
    workspace: Workspace,
    db: AsyncSession,
    custom_name: str | None = None,
    custom_description: str | None = None,
    code_verifier: str | None = None,
):
    provider = get_oauth_provider(service_name)
    if not provider:
        raise ValueError(f"Unknown OAuth service: {service_name}")

    token_data = await provider.exchange_code(code, code_verifier=code_verifier)

    service = CredentialService(db)

    # Use custom name if provided, otherwise fallback to default
    final_name = custom_name or f"{service_name.capitalize()} Account"

    credential = await service.store_credential(
        name=final_name,
        type=f"{service_name}_oauth",
        data=token_data,
        user=user,
        workspace=workspace,
        meta={
            "description": custom_description,
            "team_name": token_data.get("team_name"),
            "team_id": token_data.get("team_id"),
            "expires_at": token_data.get("expires_at"),
            "refresh_token_expires_at": token_data.get("refresh_token_expires_at"),
        },
    )
    await LogsService(db).log(
        workspace_id=workspace.id,
        user_id=user.id,
        action="credential.created",
        resource_type="credential",
        resource_id=str(credential.id),
        resource_name=credential.name,
        meta={"type": credential.type},
    )
    await db.commit()
