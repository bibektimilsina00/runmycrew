from typing import Literal

from sqlmodel import Field, SQLModel

VariableScope = Literal["workspace", "personal"]


class SecretCreate(SQLModel):
    name: str = Field(..., min_length=1, max_length=200)
    value: str = Field(default="")
    scope: VariableScope = "workspace"
    is_secret: bool = True


class SecretUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    value: str | None = None
    scope: VariableScope | None = None
    is_secret: bool | None = None


class SecretOut(SQLModel):
    id: str
    name: str
    # value only returned for non-secrets (is_secret=False)
    value: str | None
    scope: str
    is_secret: bool
    created_at: str
    updated_at: str


class SecretRevealOut(SQLModel):
    id: str
    name: str
    value: str
