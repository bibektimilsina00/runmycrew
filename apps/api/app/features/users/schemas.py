from sqlmodel import Field, SQLModel


class UserUpdate(SQLModel):
    """Schema for updating user profile information."""

    full_name: str | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, min_length=8)
