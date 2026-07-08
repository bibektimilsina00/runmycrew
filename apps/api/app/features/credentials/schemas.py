import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel


class CredentialBase(SQLModel):
    name: str
    type: str  # e.g. slack_oauth, github_pat


class CredentialCreate(CredentialBase):
    data: dict[str, Any]  # Raw sensitive data, will be encrypted
    meta: dict[str, Any] | None = None


class CredentialUpdate(SQLModel):
    name: str | None = None
    data: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


class CredentialOut(CredentialBase):
    id: uuid.UUID
    meta: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class CredentialRename(SQLModel):
    name: str


class OAuthUrlResponse(SQLModel):
    url: str
    state: str


class ProviderField(SQLModel):
    id: str
    label: str
    type: str
    placeholder: str


class ProviderOut(SQLModel):
    id: str
    name: str
    type: str
    description: str
    # theSVG slug — frontend renders the brand mark as
    # `cdn.jsdelivr.net/gh/glincker/thesvg@main/public/icons/<slug>/default.svg`.
    # When `None` the UI falls back to the provider initial.
    icon_slug: str | None = None
    # Tile background colour (CSS hex) for the brand icon.
    color: str | None = None
    fields: list[ProviderField] | None = None
    hint: str | None = None
    scopes: list[str] | None = None
    # Brand group (google/aws/microsoft/…). Frontend groups the
    # integration picker by this so a user sees one "Google" tile
    # instead of `gmail_oauth`, `gdrive_oauth`, `gcal_oauth`, … as
    # separate rows. `None` = ungrouped (stays flat).
    brand: str | None = None


class AuditLogOut(SQLModel):
    id: str
    action: str
    resource_type: str
    resource_id: str
    resource_name: str
    meta: dict[str, Any] | None
    created_at: str
    user_email: str | None
    user_name: str | None
