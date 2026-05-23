import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace, WorkspaceInvite, WorkspaceMember


class WorkspaceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: uuid.UUID) -> list[tuple[Workspace, str, int]]:
        member_count = (
            select(
                WorkspaceMember.workspace_id,
                func.count(WorkspaceMember.id).label("member_count"),
            )
            .group_by(WorkspaceMember.workspace_id)
            .subquery()
        )
        result = await self.db.execute(
            select(Workspace, WorkspaceMember.role, member_count.c.member_count)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .join(member_count, member_count.c.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.is_personal.desc(), Workspace.created_at.asc())
        )
        return [(workspace, role, int(count or 0)) for workspace, role, count in result.all()]

    async def get(self, workspace_id: uuid.UUID) -> Workspace | None:
        result = await self.db.execute(select(Workspace).where(Workspace.id == workspace_id))
        return result.scalar_one_or_none()

    async def get_member(
        self, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkspaceMember | None:
        result = await self.db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_personal_workspace(self, user_id: uuid.UUID) -> Workspace | None:
        result = await self.db.execute(
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id, Workspace.is_personal.is_(True))
            .order_by(Workspace.created_at.asc())
        )
        return result.scalars().first()

    async def create_workspace(
        self, name: str, slug: str, owner_id: uuid.UUID, is_personal: bool = False
    ) -> Workspace:
        workspace = Workspace(name=name, slug=slug, owner_id=owner_id, is_personal=is_personal)
        self.db.add(workspace)
        await self.db.flush()
        self.db.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner_id, role="owner"))
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def slug_exists(self, slug: str) -> bool:
        result = await self.db.execute(select(Workspace.id).where(Workspace.slug == slug))
        return result.scalar_one_or_none() is not None

    async def list_members(self, workspace_id: uuid.UUID) -> list[WorkspaceMember]:
        result = await self.db.execute(
            select(WorkspaceMember)
            .options(selectinload(WorkspaceMember.user))
            .where(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.joined_at.asc())
        )
        return list(result.scalars().all())

    async def get_invite_by_token(self, token: str) -> WorkspaceInvite | None:
        result = await self.db.execute(
            select(WorkspaceInvite)
            .options(selectinload(WorkspaceInvite.workspace))
            .where(WorkspaceInvite.token == token)
        )
        return result.scalar_one_or_none()

    async def create_invite(
        self,
        workspace_id: uuid.UUID,
        email: str,
        role: str,
        token: str,
        invited_by: uuid.UUID,
        expires_at: datetime,
    ) -> WorkspaceInvite:
        invite = WorkspaceInvite(
            workspace_id=workspace_id,
            email=email.lower(),
            role=role,
            token=token,
            invited_by=invited_by,
            expires_at=expires_at,
        )
        self.db.add(invite)
        await self.db.commit()
        await self.db.refresh(invite)
        return invite

    async def accept_invite(self, invite: WorkspaceInvite, user: User) -> WorkspaceMember:
        member = await self.get_member(invite.workspace_id, user.id)
        if member is None:
            member = WorkspaceMember(
                workspace_id=invite.workspace_id,
                user_id=user.id,
                role=invite.role,
                invited_by=invite.invited_by,
            )
            self.db.add(member)
        invite.accepted_at = datetime.now(UTC)
        await self.db.commit()
        result = await self.db.execute(
            select(WorkspaceMember)
            .options(selectinload(WorkspaceMember.user))
            .where(WorkspaceMember.id == member.id)
        )
        loaded = result.scalar_one()
        return loaded

    async def update_member_role(self, member: WorkspaceMember, role: str) -> WorkspaceMember:
        member.role = role
        await self.db.commit()
        result = await self.db.execute(
            select(WorkspaceMember)
            .options(selectinload(WorkspaceMember.user))
            .where(WorkspaceMember.id == member.id)
        )
        return result.scalar_one()

    async def delete_member(self, member: WorkspaceMember) -> None:
        await self.db.delete(member)
        await self.db.commit()

    async def update_workspace(self, workspace: Workspace, name: str, slug: str) -> Workspace:
        workspace.name = name
        workspace.slug = slug
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def delete_workspace(self, workspace: Workspace) -> None:
        await self.db.delete(workspace)
        await self.db.commit()
