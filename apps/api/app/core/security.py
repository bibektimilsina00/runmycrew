from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt

from apps.api.app.core.config import settings

ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user_from_token(token: str) -> Any | None:
    """
    Decodes a JWT token and returns the user object.
    Used for WebSocket authentication.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email or not isinstance(email, str):
            return None

        from apps.api.app.core.database import AsyncSessionLocal
        from apps.api.app.features.users.repository import UserRepository

        async with AsyncSessionLocal() as db:
            user_repo = UserRepository(db)
            user = await user_repo.get_by_email(email=email)
            return user
    except Exception:
        return None
