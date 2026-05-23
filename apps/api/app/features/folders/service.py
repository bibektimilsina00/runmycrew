import uuid
from collections.abc import Sequence

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.folders.models import Folder
from apps.api.app.features.folders.schemas import FolderCreate, FolderUpdate
from apps.api.app.features.workflows.models import Workflow


class FolderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_folder(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, schema: FolderCreate
    ) -> Folder:
        folder = Folder(
            user_id=user_id,
            workspace_id=workspace_id,
            name=schema.name,
            parent_id=schema.parent_id,
        )
        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)
        return folder

    async def get_folders(self, workspace_id: uuid.UUID) -> Sequence[Folder]:
        stmt = select(Folder).where(Folder.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_folder(self, workspace_id: uuid.UUID, folder_id: uuid.UUID) -> Folder | None:
        stmt = select(Folder).where(Folder.id == folder_id, Folder.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def update_folder(
        self, workspace_id: uuid.UUID, folder_id: uuid.UUID, schema: FolderUpdate
    ) -> Folder | None:
        folder = await self.get_folder(workspace_id, folder_id)
        if not folder:
            return None

        if schema.name is not None:
            folder.name = schema.name
        if schema.parent_id is not None:
            folder.parent_id = schema.parent_id

        await self.db.commit()
        await self.db.refresh(folder)
        return folder

    async def delete_folder(self, workspace_id: uuid.UUID, folder_id: uuid.UUID) -> bool:
        folder = await self.get_folder(workspace_id, folder_id)
        if not folder:
            return False

        await self.db.execute(
            delete(Workflow).where(
                Workflow.folder_id == folder_id, Workflow.workspace_id == workspace_id
            )
        )

        await self.db.delete(folder)
        await self.db.commit()
        return True


def get_folder_service(db: AsyncSession = Depends(get_db)) -> FolderService:
    return FolderService(db)
