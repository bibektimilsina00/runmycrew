from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class SkillCreate(SQLModel):
    name: str = Field(
        min_length=1,
        max_length=64,
        regex=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        description="name must be kebab-case (a-z0-9 and hyphens)",
    )
    description: str = Field(default="", max_length=1024)
    icon: str = Field(default="BookOpen", min_length=1, max_length=64)
    color: str = Field(default="#8b5cf6", min_length=1, max_length=32)
    content: str = Field(min_length=1, max_length=50_000)


class SkillUpdate(SQLModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        regex=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        description="name must be kebab-case (a-z0-9 and hyphens)",
    )
    description: str | None = Field(default=None, max_length=1024)
    icon: str | None = Field(default=None, min_length=1, max_length=64)
    color: str | None = Field(default=None, min_length=1, max_length=32)
    content: str | None = Field(default=None, min_length=1, max_length=50_000)


class SkillOut(SQLModel):
    id: uuid.UUID
    name: str
    description: str
    icon: str
    color: str
    content: str
    created_at: datetime
    updated_at: datetime


class SkillMetaOut(SQLModel):
    """Lightweight metadata — no content. Used for tool selector listings."""

    id: uuid.UUID
    name: str
    description: str
    icon: str
    color: str
    created_at: datetime
    updated_at: datetime
