import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CredentialBase(BaseModel):
    name: str
    type: str  # e.g. slack_oauth, github_pat


class CredentialCreate(CredentialBase):
    data: dict[str, Any]  # Raw sensitive data, will be encrypted
    meta: dict[str, Any] | None = None


class CredentialUpdate(BaseModel):
    name: str | None = None
    data: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


class CredentialOut(CredentialBase):
    id: uuid.UUID
    meta: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CredentialRename(BaseModel):
    name: str


class OAuthUrlResponse(BaseModel):
    url: str
    state: str


class ProviderField(BaseModel):
    id: str
    label: str
    type: str
    placeholder: str


class ProviderOut(BaseModel):
    id: str
    name: str
    type: str
    description: str
    icon_url: str | None = None
    fields: list[ProviderField] | None = None
    hint: str | None = None
    scopes: list[str] | None = None
