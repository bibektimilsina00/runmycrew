import secrets
import uuid
from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.api.v1.workspaces.dependencies import get_current_workspace
from apps.api.app.core.database import get_db
from apps.api.app.credential_manager.api_keys import PROVIDERS as API_KEY_PROVIDERS
from apps.api.app.credential_manager.oauth.flow import PROVIDERS as OAUTH_PROVIDERS
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace, WorkspaceMember
from apps.api.app.schemas.credential import (
    CredentialCreate,
    CredentialOut,
    CredentialRename,
    OAuthUrlResponse,
    ProviderOut,
)
from apps.api.app.services.audit_service import AuditService
from apps.api.app.services.credential_service import CredentialService

router = APIRouter()

MANAGE_ROLES = {"owner", "admin"}


async def _require_manage_credentials(
    current_user: User, workspace: Workspace, db: AsyncSession
) -> None:
    """Only owners and admins can create/rename/delete workspace connections."""
    result = await db.execute(
        sa.select(WorkspaceMember.role).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    role = result.scalar_one_or_none()
    if role not in MANAGE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can manage connections.",
        )


@router.get("/providers", response_model=list[ProviderOut])
async def list_providers():
    providers = []

    # Collect OAuth providers
    for p in OAUTH_PROVIDERS.values():
        providers.append(
            {
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "description": p.description,
                "icon_url": p.icon_url,
                "fields": getattr(p, "fields", None),
                "hint": getattr(p, "hint", None),
                "scopes": getattr(p, "scopes", None),
            }
        )

    # Collect API Key providers
    for p in API_KEY_PROVIDERS.values():
        providers.append(
            {
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "description": p.description,
                "icon_url": p.icon_url,
                "fields": p.fields,
                "hint": p.hint,
                "scopes": getattr(p, "scopes", None),
            }
        )

    return providers


@router.get("/", response_model=list[CredentialOut])
async def list_credentials(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    service = CredentialService(db)
    return await service.list_credentials(current_user, workspace)


class AuditLogOut(BaseModel):
    id: str
    action: str
    resource_type: str
    resource_id: str
    resource_name: str
    meta: dict[str, Any] | None
    created_at: str
    user_email: str | None
    user_name: str | None


@router.get("/audit", response_model=list[AuditLogOut])
async def list_audit_log(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    entries = await AuditService(db).list_for_workspace(
        workspace_id=workspace.id,
        resource_type="credential",
        limit=100,
    )
    return [
        AuditLogOut(
            id=str(e.id),
            action=e.action,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            resource_name=e.resource_name,
            meta=e.meta,
            created_at=e.created_at.isoformat(),
            user_email=e.user.email if e.user else None,
            user_name=e.user.full_name if e.user else None,
        )
        for e in entries
    ]


@router.post("/", response_model=CredentialOut, status_code=status.HTTP_201_CREATED)
async def create_credential(
    data: CredentialCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _require_manage_credentials(current_user, workspace, db)
    service = CredentialService(db)
    credential = await service.store_credential(
        name=data.name,
        type=data.type,
        data=data.data,
        user=current_user,
        workspace=workspace,
    )
    await AuditService(db).log(
        workspace_id=workspace.id,
        user_id=current_user.id,
        action="credential.created",
        resource_type="credential",
        resource_id=str(credential.id),
        resource_name=credential.name,
        meta={"type": credential.type},
    )
    await db.commit()
    return credential


@router.patch("/{credential_id}", response_model=CredentialOut)
async def rename_credential(
    credential_id: uuid.UUID,
    data: CredentialRename,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _require_manage_credentials(current_user, workspace, db)
    service = CredentialService(db)
    old = await service.repo.get_by_id_and_workspace(credential_id, workspace.id)
    old_name = old.name if old else str(credential_id)
    credential = await service.rename_credential(credential_id, data.name, current_user, workspace)
    await AuditService(db).log(
        workspace_id=workspace.id,
        user_id=current_user.id,
        action="credential.renamed",
        resource_type="credential",
        resource_id=str(credential.id),
        resource_name=credential.name,
        meta={"old_name": old_name, "new_name": credential.name},
    )
    await db.commit()
    return credential


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _require_manage_credentials(current_user, workspace, db)
    service = CredentialService(db)
    cred = await service.repo.get_by_id_and_workspace(credential_id, workspace.id)
    cred_name = cred.name if cred else str(credential_id)
    cred_type = cred.type if cred else ""
    await service.delete_credential(credential_id, current_user, workspace)
    await AuditService(db).log(
        workspace_id=workspace.id,
        user_id=current_user.id,
        action="credential.deleted",
        resource_type="credential",
        resource_id=str(credential_id),
        resource_name=cred_name,
        meta={"type": cred_type},
    )
    await db.commit()


@router.get("/oauth/{service_name}/url", response_model=OAuthUrlResponse)
async def get_oauth_url(
    service_name: str,
    name: str | None = None,
    description: str | None = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _require_manage_credentials(current_user, workspace, db)
    try:
        from apps.api.app.credential_manager.oauth.flow import get_oauth_provider

        provider = get_oauth_provider(service_name)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown OAuth service: {service_name}",
            )

        # Include metadata in state to retrieve on callback
        import base64
        import hashlib
        import json

        state_data = {
            "nonce": secrets.token_urlsafe(16),
            "name": name,
            "description": description,
            "user_id": str(current_user.id),
            "workspace_id": str(workspace.id),
        }

        # Add PKCE for Slack
        code_challenge = None
        if service_name == "slack":
            code_verifier = secrets.token_urlsafe(64)
            state_data["code_verifier"] = code_verifier
            # SHA256 hash of verifier, then base64url encoded
            challenge_hash = hashlib.sha256(code_verifier.encode()).digest()
            code_challenge = base64.urlsafe_b64encode(challenge_hash).decode().replace("=", "")

        state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

        if service_name == "slack":
            url = provider.get_authorization_url(state=state, code_challenge=code_challenge)
        else:
            url = provider.get_authorization_url(state=state)

        return OAuthUrlResponse(url=url, state=state)
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth flow not yet implemented",
        ) from exc


@router.get("/oauth/{service_name}/callback")
async def oauth_callback(
    service_name: str,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        # Decode metadata from state
        import base64
        import binascii
        import json

        try:
            state_data = json.loads(base64.urlsafe_b64decode(state).decode())
            custom_name = state_data.get("name")
            custom_description = state_data.get("description")
            code_verifier = state_data.get("code_verifier")
            user_id = state_data.get("user_id")
            workspace_id = state_data.get("workspace_id")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            custom_name = None
            custom_description = None
            code_verifier = None
            user_id = None
            workspace_id = None

        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid state: user_id missing")
        if not workspace_id:
            raise HTTPException(status_code=400, detail="Invalid state: workspace_id missing")

        from sqlalchemy import select

        from apps.api.app.models.user import User

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        from apps.api.app.services.workspace_service import WorkspaceService

        workspace = await WorkspaceService(db).resolve_workspace(user, uuid.UUID(workspace_id))

        from apps.api.app.credential_manager.oauth.callback import handle_oauth_callback

        await handle_oauth_callback(
            service_name=service_name,
            code=code,
            user=user,
            workspace=workspace,
            db=db,
            custom_name=custom_name,
            custom_description=custom_description,
            code_verifier=code_verifier,
        )
        from apps.api.app.core.config import settings

        # Redirect back to frontend integrations settings page
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings/integrations")
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth callback not yet implemented",
        ) from exc
