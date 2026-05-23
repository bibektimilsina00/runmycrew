from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher, exceptions
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import logger
from apps.api.app.core.service import BaseService
from apps.api.app.features.auth.schemas import UserLogin, UserRegister
from apps.api.app.features.users.models import User
from apps.api.app.features.users.repository import UserRepository
from apps.api.app.features.workspaces.service import WorkspaceService

ph = PasswordHasher()


class AuthService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.user_repo = UserRepository(db)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return ph.verify(hashed_password, plain_password)
        except exceptions.VerifyMismatchError:
            return False

    def get_password_hash(self, password: str) -> str:
        return ph.hash(password)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def register(self, user_in: UserRegister) -> User:
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
            )

        full_name = user_in.full_name.strip() if user_in.full_name else None
        user = User(
            email=user_in.email,
            hashed_password=self.get_password_hash(user_in.password),
            full_name=full_name or None,
        )
        self.db.add(user)
        await self.db.flush()
        await WorkspaceService(self.db).create_personal_workspace(user)
        await self.db.refresh(user)
        return user

    async def authenticate(self, user_login: UserLogin) -> User | None:
        user = await self.user_repo.get_by_email(user_login.email)
        if not user:
            return None
        if not self.verify_password(user_login.password, user.hashed_password):
            return None
        return user

    async def forgot_password(self, email: str) -> bool:
        user = await self.user_repo.get_by_email(email)
        if not user:
            # For security, we return True even if user doesn't exist
            # to prevent email enumeration
            return True

        # Generate a password reset token (15 mins expiry)
        reset_token = self.create_access_token(
            data={"sub": user.email, "type": "password_reset"}, expires_delta=timedelta(minutes=15)
        )

        # MOCK EMAIL SENDING
        # In a real app, you would use an email service (SendGrid, Mailgun, etc.)
        logger.info(
            f"PASSWORD RESET LINK for {email}: http://localhost:5173/reset-password?token={reset_token}"
        )

        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str | None = payload.get("sub")
            token_type: str | None = payload.get("type")

            if email is None or token_type != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired reset token",
                )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired reset token",
            ) from exc

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.hashed_password = self.get_password_hash(new_password)
        await self.user_repo.update(user)
        return True


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)
