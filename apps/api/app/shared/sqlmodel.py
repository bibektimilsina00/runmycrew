from datetime import UTC, datetime

from sqlmodel import SQLModel


class SQLModelBase(SQLModel):
    """Base class for SQLModel-backed feature models."""


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)
