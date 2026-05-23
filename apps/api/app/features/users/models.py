from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import relationship
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, utc_now

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
    created_at: datetime = Field(default_factory=utc_now)

    workflows: list[Workflow] = Relationship(sa_relationship=relationship("Workflow", 
        back_populates="user", cascade="all, delete-orphan")
    )
    folders: list[Folder] = Relationship(sa_relationship=relationship("Folder", 
        back_populates="user", cascade="all, delete-orphan")
    )
    credentials: list[Credential] = Relationship(sa_relationship=relationship("Credential", 
        back_populates="user", cascade="all, delete-orphan")
    )
    skills: list[Skill] = Relationship(sa_relationship=relationship("Skill", 
        back_populates="user", cascade="all, delete-orphan")
    )
    api_keys: list[ApiKey] = Relationship(sa_relationship=relationship("ApiKey", 
        back_populates="user", cascade="all, delete-orphan")
    )
    workspace_memberships: list[WorkspaceMember] = Relationship(sa_relationship=relationship("WorkspaceMember", 
        back_populates="user",
        foreign_keys="[WorkspaceMember.user_id]", lazy="select",)
    )


import apps.api.app.features.api_keys.models  # noqa: E402,F401
import apps.api.app.features.credentials.models  # noqa: E402,F401
import apps.api.app.features.folders.models  # noqa: E402,F401
import apps.api.app.features.skills.models  # noqa: E402,F401
import apps.api.app.features.workflows.models  # noqa: E402,F401
import apps.api.app.features.workspaces.models  # noqa: E402,F401
