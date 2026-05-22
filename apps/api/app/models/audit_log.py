import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.models.base import Base

if TYPE_CHECKING:
    from apps.api.app.models.user import User


def _now() -> datetime:
    return datetime.now(UTC)


class AuditLog(Base):
    """Immutable record of user actions on workspace resources."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspace.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,   # nullable so logs survive user deletion
        index=True,
    )
    # e.g. "credential.created", "credential.renamed", "credential.deleted"
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. "credential"
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # stringified UUID of the affected resource
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # human-readable name of the resource at the time of the action
    resource_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # extra context: {"old_name": "...", "new_name": "..."} for renames etc.
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id], lazy="joined")
