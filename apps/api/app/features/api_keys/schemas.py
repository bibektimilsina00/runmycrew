from datetime import datetime
from uuid import UUID

from sqlmodel import Field, SQLModel


class ApiKeyCreate(SQLModel):
    """Schema for creating a new API Key."""

    name: str = Field(..., min_length=1, max_length=200)


class ApiKeyOut(SQLModel):
    """Schema representing an existing API key's metadata."""

    id: UUID
    name: str
    key_preview: str
    created_at: datetime


class ApiKeyCreateResponse(SQLModel):
    """Schema representing the response when creating a new API key, containing the plaintext token."""

    id: UUID
    name: str
    key_preview: str
    created_at: datetime
    token: str
