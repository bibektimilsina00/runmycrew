from dataclasses import dataclass
from typing import Protocol

from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class InviteEmail:
    to_email: str
    workspace_name: str
    inviter_email: str
    invite_url: str
    role: str


class EmailProvider(Protocol):
    async def send_workspace_invite(self, email: InviteEmail) -> None:
        """Send a workspace invite email."""


class DevEmailProvider:
    async def send_workspace_invite(self, email: InviteEmail) -> None:
        """Log invite emails in development until a production provider is configured."""
        logger.info(
            "Workspace invite email to %s for %s as %s from %s: %s",
            email.to_email,
            email.workspace_name,
            email.role,
            email.inviter_email,
            email.invite_url,
        )


class EmailService:
    def __init__(self, provider: EmailProvider | None = None):
        self.provider = provider or DevEmailProvider()

    async def send_workspace_invite(self, email: InviteEmail) -> None:
        await self.provider.send_workspace_invite(email)
