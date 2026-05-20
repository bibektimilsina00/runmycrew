import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.models.user import User
from apps.api.app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceInviteCreate,
    WorkspaceInviteOut,
    WorkspaceInvitePreviewOut,
    WorkspaceMemberOut,
    WorkspaceMemberUpdate,
    WorkspaceWithRoleOut,
)
from apps.api.app.services.workspace_service import WorkspaceService

router = APIRouter()


def _workspace_with_role(workspace, role: str, member_count: int) -> WorkspaceWithRoleOut:
    return WorkspaceWithRoleOut(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        owner_id=workspace.owner_id,
        is_personal=workspace.is_personal,
        avatar_url=workspace.avatar_url,
        plan=workspace.plan,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        role=role,
        member_count=member_count,
    )


@router.get("/", response_model=list[WorkspaceWithRoleOut])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await WorkspaceService(db).list_workspaces(current_user)
    return [_workspace_with_role(workspace, role, member_count) for workspace, role, member_count in rows]


@router.post("/", response_model=WorkspaceWithRoleOut, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workspace = await WorkspaceService(db).create_workspace(data, current_user)
    return _workspace_with_role(workspace, "owner", 1)


@router.get("/invites/{token}", response_model=WorkspaceInvitePreviewOut)
async def preview_invite(token: str, db: AsyncSession = Depends(get_db)):
    invite = await WorkspaceService(db).preview_invite(token)
    return WorkspaceInvitePreviewOut(
        workspace_id=invite.workspace_id,
        workspace_name=invite.workspace.name,
        email=invite.email,
        role=invite.role,
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at,
    )


@router.post("/invites/{token}/accept", response_model=WorkspaceMemberOut)
async def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceService(db).accept_invite(token, current_user)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberOut])
async def list_members(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceService(db).list_members(workspace_id, current_user)


@router.post("/{workspace_id}/invites", response_model=WorkspaceInviteOut, status_code=status.HTTP_201_CREATED)
async def create_invite(
    workspace_id: uuid.UUID,
    data: WorkspaceInviteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    invite, invite_url = await WorkspaceService(db).create_invite(workspace_id, data, current_user)
    return WorkspaceInviteOut(
        id=invite.id,
        workspace_id=invite.workspace_id,
        email=invite.email,
        role=invite.role,
        token=invite.token,
        invite_url=invite_url,
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at,
        created_at=invite.created_at,
    )


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberOut)
async def update_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    data: WorkspaceMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await WorkspaceService(db).update_member_role(workspace_id, user_id, data.role, current_user)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).remove_member(workspace_id, user_id, current_user)
