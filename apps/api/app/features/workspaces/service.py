import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace, WorkspaceInvite, WorkspaceMember
from apps.api.app.features.workspaces.repository import WorkspaceRepository
from apps.api.app.features.workspaces.schemas import WorkspaceCreate, WorkspaceInviteCreate
from apps.api.app.utils.email_service import EmailService, InviteEmail

MANAGE_MEMBER_ROLES = {"owner", "admin"}
EDIT_ROLES = {"owner", "admin", "member"}
ROLE_RANK = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}


class WorkspaceService:
    def __init__(self, db: AsyncSession, email_service: EmailService | None = None):
        self.repo = WorkspaceRepository(db)
        self.email_service = email_service or EmailService()

    async def list_workspaces(self, user: User) -> list[tuple[Workspace, str, int]]:
        return await self.repo.list_for_user(user.id)

    async def create_workspace(self, data: WorkspaceCreate, user: User) -> Workspace:
        slug = await self._unique_slug(data.name)
        workspace = await self.repo.create_workspace(data.name.strip(), slug, user.id)
        await self._ensure_default_workflow(workspace)
        return workspace

    async def create_personal_workspace(self, user: User) -> Workspace:
        existing = await self.repo.get_personal_workspace(user.id)
        if existing:
            await self._ensure_default_workflow(existing)
            return existing
        owner_name = self._personal_workspace_owner_name(user)
        workspace_name = f"{owner_name}'s Workspace"
        slug = await self._unique_slug(workspace_name)
        workspace = await self.repo.create_workspace(
            workspace_name, slug, user.id, is_personal=True
        )
        await self._ensure_default_workflow(workspace)
        return workspace

    async def resolve_workspace(self, user: User, workspace_id: uuid.UUID | None) -> Workspace:
        workspace = (
            await self.repo.get(workspace_id)
            if workspace_id is not None
            else await self.repo.get_personal_workspace(user.id)
        )
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        await self.require_member(workspace.id, user)
        return workspace

    async def require_member(self, workspace_id: uuid.UUID, user: User) -> WorkspaceMember:
        member = await self.repo.get_member(workspace_id, user.id)
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied"
            )
        return member

    async def require_edit(self, workspace_id: uuid.UUID, user: User) -> WorkspaceMember:
        member = await self.require_member(workspace_id, user)
        if member.role not in EDIT_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Workspace is read-only"
            )
        return member

    async def require_manage_members(self, workspace_id: uuid.UUID, user: User) -> WorkspaceMember:
        member = await self.require_member(workspace_id, user)
        if member.role not in MANAGE_MEMBER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot manage workspace members",
            )
        return member

    async def list_members(self, workspace_id: uuid.UUID, user: User) -> list[WorkspaceMember]:
        await self.require_member(workspace_id, user)
        return await self.repo.list_members(workspace_id)

    async def create_invite(
        self,
        workspace_id: uuid.UUID,
        data: WorkspaceInviteCreate,
        inviter: User,
    ) -> tuple[WorkspaceInvite, str]:
        await self.require_manage_members(workspace_id, inviter)
        workspace = await self.repo.get(workspace_id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(days=7)
        invite = await self.repo.create_invite(
            workspace_id=workspace_id,
            email=str(data.email),
            role=data.role,
            token=token,
            invited_by=inviter.id,
            expires_at=expires_at,
        )
        invite_url = f"{settings.FRONTEND_URL}/invites/{token}"
        if data.send_email:
            await self.email_service.send_workspace_invite(
                InviteEmail(
                    to_email=str(data.email),
                    workspace_name=workspace.name,
                    inviter_email=inviter.email,
                    invite_url=invite_url,
                    role=data.role,
                )
            )
        return invite, invite_url

    async def preview_invite(self, token: str) -> WorkspaceInvite:
        invite = await self.repo.get_invite_by_token(token)
        if invite is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
        return invite

    async def accept_invite(self, token: str, user: User) -> WorkspaceMember:
        invite = await self.preview_invite(token)
        now = datetime.now(UTC)
        expires_at = (
            invite.expires_at if invite.expires_at.tzinfo else invite.expires_at.replace(tzinfo=UTC)
        )
        if invite.accepted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Invite already accepted"
            )
        if expires_at <= now:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite expired")
        if invite.email.lower() != user.email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invite is for a different email"
            )
        return await self.repo.accept_invite(invite, user)

    async def update_member_role(
        self,
        workspace_id: uuid.UUID,
        target_user_id: uuid.UUID,
        role: str,
        actor: User,
    ) -> WorkspaceMember:
        actor_member = await self.require_manage_members(workspace_id, actor)
        target = await self.repo.get_member(workspace_id, target_user_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        self._assert_can_manage_target(actor_member, target, role)
        return await self.repo.update_member_role(target, role)

    async def update_workspace(
        self,
        workspace_id: uuid.UUID,
        name: str,
        actor: User,
    ) -> Workspace:
        workspace = await self.repo.get(workspace_id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        member = await self.repo.get_member(workspace_id, actor.id)
        if not member or member.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can rename the workspace"
            )
        new_slug = await self._unique_slug_for_rename(name, workspace.slug)
        return await self.repo.update_workspace(workspace, name.strip(), new_slug)

    async def delete_workspace(
        self,
        workspace_id: uuid.UUID,
        actor: User,
    ) -> None:
        workspace = await self.repo.get(workspace_id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        if workspace.is_personal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete personal workspace"
            )
        member = await self.repo.get_member(workspace_id, actor.id)
        if not member or member.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can delete the workspace"
            )
        await self.repo.delete_workspace(workspace)

    async def remove_member(
        self,
        workspace_id: uuid.UUID,
        target_user_id: uuid.UUID,
        actor: User,
    ) -> None:
        actor_member = await self.require_manage_members(workspace_id, actor)
        target = await self.repo.get_member(workspace_id, target_user_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        self._assert_can_manage_target(actor_member, target, None)
        await self.repo.delete_member(target)

    async def _unique_slug_for_rename(self, name: str, current_slug: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:80] or "workspace"
        # If the new base matches the current slug (ignoring numeric suffix), keep it
        if current_slug == base or current_slug.startswith(base + "-"):
            return current_slug
        slug = base
        suffix = 2
        while await self.repo.slug_exists(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    async def _unique_slug(self, name: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:80] or "workspace"
        slug = base
        suffix = 2
        while await self.repo.slug_exists(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def _personal_workspace_owner_name(self, user: User) -> str:
        source = (user.full_name or "").strip() or user.email.split("@", 1)[0]
        first_name = re.split(r"\s+", source.strip(), maxsplit=1)[0]
        cleaned = re.sub(r"[^A-Za-z0-9_-]+", "", first_name).strip("_-")
        if not cleaned:
            return "My"
        normalized = f"{cleaned[0].upper()}{cleaned[1:]}"
        return normalized[:40]

    async def _ensure_default_workflow(self, workspace: Workspace) -> None:
        from apps.api.app.features.workflows.service import WorkflowService

        workflows = await WorkflowService(self.repo.db).repository.list_by_workspace(workspace.id)
        if not workflows:
            await WorkflowService(self.repo.db).ensure_default_workflow(workspace)

    def _assert_can_manage_target(
        self, actor: WorkspaceMember, target: WorkspaceMember, new_role: str | None
    ) -> None:
        if target.role == "owner" and target.user_id != actor.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Owners cannot be modified"
            )
        if actor.role != "owner" and ROLE_RANK[target.role] >= ROLE_RANK[actor.role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot manage this member"
            )
        if new_role == "owner" and actor.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can assign owner"
            )
