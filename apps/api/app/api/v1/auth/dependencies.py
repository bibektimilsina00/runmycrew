import hashlib

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.models.user import User
from apps.api.app.repositories.api_key_repository import ApiKeyRepository
from apps.api.app.repositories.user_repository import UserRepository

# Set auto_error=False to prevent automatic 401 failure when the header is missing,
# allowing us to check x-api-key or Authorization headers manually.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False
)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
) -> User:
    """Retrieve and authenticate the current user.

    Supports authentication via:
    1. HTTP header 'x-api-key' (developer access token)
    2. Bearer token starting with 'fuse_live_' inside Authorization header
    3. Standard JWT Access Token inside Authorization header
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Check for API key in x-api-key header or Bearer fuse_live_ token
    api_key = request.headers.get("x-api-key")

    if not api_key and token and token.startswith("fuse_live_"):
        api_key = token

    if not api_key:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer fuse_live_"):
            parts = auth_header.split(" ", 1)
            if len(parts) == 2:
                api_key = parts[1]

    if api_key:
        # Securely hash the input key using SHA-256 for DB lookup
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        api_key_repo = ApiKeyRepository(db)
        key_record = await api_key_repo.get_by_hash(key_hash)

        if not key_record:
            raise credentials_exception

        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(key_record.user_id)
        if not user or not user.is_active:
            raise credentials_exception

        return user

    # 2. Fallback to JWT validation if no API key was provided
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        email: str = sub
    except JWTError:
        raise credentials_exception from None

    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email=email)
    if user is None or not user.is_active:
        raise credentials_exception

    return user
