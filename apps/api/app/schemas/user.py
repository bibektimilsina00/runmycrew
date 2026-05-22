from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserUpdate(BaseModel):
    """Schema for updating user profile information."""

    full_name: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, min_length=8)


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API Key."""

    name: str = Field(..., min_length=1, max_length=200)


class ApiKeyOut(BaseModel):
    """Schema representing an existing API key's metadata."""

    id: UUID
    name: str
    key_preview: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    """Schema representing the response when creating a new API key, containing the plaintext token."""

    id: UUID
    name: str
    key_preview: str
    created_at: datetime
    token: str

    class Config:
        from_attributes = True
