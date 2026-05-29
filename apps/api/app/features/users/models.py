import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field

if TYPE_CHECKING:
    from apps.api.app.features.api_keys.models import ApiKey
    from apps.api.app.features.credentials.models import Credential
    from apps.api.app.features.folders.models import Folder
    from apps.api.app.features.skills.models import Skill
    from apps.api.app.features.workflows.models import Workflow
    from apps.api.app.features.workspaces.models import WorkspaceMember


class User(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    full_name: str | None = Field(default=None, max_length=200)
    avatar_url: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = created_at_field()

    workflows: list["Workflow"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    folders: list["Folder"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    credentials: list["Credential"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    skills: list["Skill"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    api_keys: list["ApiKey"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    workspace_memberships: list["WorkspaceMember"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[WorkspaceMember.user_id]", "lazy": "select"},
    )


from apps.api.app.features.api_keys.models import ApiKey  # noqa: E402,F401
from apps.api.app.features.credentials.models import Credential  # noqa: E402,F401
from apps.api.app.features.folders.models import Folder  # noqa: E402,F401
from apps.api.app.features.skills.models import Skill  # noqa: E402,F401
from apps.api.app.features.workflows.models import Workflow  # noqa: E402,F401
from apps.api.app.features.workspaces.models import WorkspaceMember  # noqa: E402,F401
