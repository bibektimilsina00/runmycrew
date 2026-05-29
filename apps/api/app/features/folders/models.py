import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field, updated_at_field

if TYPE_CHECKING:
    from apps.api.app.features.users.models import User
    from apps.api.app.features.workflows.models import Workflow


class Folder(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field()
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="folder.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()

    user: "User" = Relationship(back_populates="folders")
    parent: "Folder" = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Folder.id"}
    )
    children: list["Folder"] = Relationship(
        back_populates="parent", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    workflows: list["Workflow"] = Relationship(
        back_populates="folder", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
