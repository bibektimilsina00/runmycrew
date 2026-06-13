from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class SkillCreate(SQLModel):
    # Free-form human-readable name. The agent system prompt and the
    # `load_skill` tool use this string verbatim as the lookup key, so
    # it doubles as the identifier — but the agent injection escapes
    # XML-unsafe characters, so any printable text is safe to store.
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=1024)
    icon: str = Field(default="BookOpen", min_length=1, max_length=64)
    color: str = Field(default="#8b5cf6", min_length=1, max_length=32)
    content: str = Field(default="", max_length=50_000)


class SkillUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=1024)
    icon: str | None = Field(default=None, min_length=1, max_length=64)
    color: str | None = Field(default=None, min_length=1, max_length=32)
    content: str | None = Field(default=None, max_length=50_000)


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
