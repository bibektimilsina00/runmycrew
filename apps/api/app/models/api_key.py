import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.app.models.user import User

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.models.base import Base


class ApiKey(Base):
    """Developer API Key model for authenticating CLI tools and services.

    Attributes:
        id: Unique identifier of the API key.
        user_id: ID of the user that owns this API key.
        name: User-defined descriptive name/label for the key.
        key_hash: Cryptographic SHA-256 hash of the generated key.
        key_preview: Masked visual preview of the key.
        created_at: Timestamp when the key was generated.
    """

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    key_preview: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None)
    )

    user: Mapped["User"] = relationship("User", back_populates="api_keys")
