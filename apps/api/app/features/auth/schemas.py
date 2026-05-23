from datetime import datetime
from uuid import UUID

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    email: EmailStr


class UserRegister(UserBase):
    password: str = Field(..., min_length=8)
    full_name: str | None = Field(default=None, max_length=200)


class UserLogin(UserBase):
    password: str


class UserOut(UserBase):
    id: UUID
    full_name: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class ForgotPasswordRequest(SQLModel):
    email: EmailStr


class ResetPasswordRequest(SQLModel):
    token: str
    new_password: str = Field(..., min_length=8)


class MessageResponse(SQLModel):
    message: str
