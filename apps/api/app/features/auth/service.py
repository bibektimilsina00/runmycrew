import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from argon2 import PasswordHasher, exceptions
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.core.service import BaseService
from apps.api.app.features.auth.schemas import UserLogin, UserRegister
from apps.api.app.features.users.models import User
from apps.api.app.features.users.repository import UserRepository
from apps.api.app.features.workspaces.service import WorkspaceService
from apps.api.app.utils.email_service import EmailService, PasswordResetEmail

ph = PasswordHasher()


RESET_TOKEN_EXPIRES_MINUTES = 15

# Google OAuth — sign-in flow. Scopes are intentionally minimal
# (openid + email + profile); broader product scopes (Gmail, Drive,
# Calendar, etc.) are requested separately by credential_manager
# when the user actually connects those apps.
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_LOGIN_SCOPES = "openid email profile"
GOOGLE_STATE_EXPIRES_MINUTES = 10


class AuthService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.user_repo = UserRepository(db)
        # Auto-selects DevEmailProvider when SMTP_HOST is unset, so
        # local dev keeps logging the reset link instead of sending.
        self.email_service = EmailService()

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
        # OAuth-only accounts have no password — block password login
        # rather than silently failing with a confusing "wrong password".
        if user.hashed_password is None:
            return None
        if not self.verify_password(user_login.password, user.hashed_password):
            return None
        return user

    # ── Google sign-in ────────────────────────────────────────────────
    @staticmethod
    def _google_redirect_uri() -> str:
        # Mounted under API_V1_STR in main.py — same prefix as the rest
        # of the auth router. Google Cloud Console must list this exact
        # URI under "Authorized redirect URIs" for the OAuth client.
        return f"{settings.BASE_URL.rstrip('/')}{settings.API_V1_STR}/auth/google/callback"

    def _mint_oauth_state(self, next_path: str) -> str:
        # Signed, short-lived state defends against CSRF on the callback.
        # `nonce` makes each redirect unique so an attacker can't replay
        # a stale state; `next` carries the post-login redirect.
        payload = {
            "nonce": secrets.token_urlsafe(16),
            "next": next_path,
            "type": "oauth_state",
            "exp": datetime.now(UTC) + timedelta(minutes=GOOGLE_STATE_EXPIRES_MINUTES),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def _verify_oauth_state(self, state: str) -> str:
        try:
            payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state",
            ) from exc
        if payload.get("type") != "oauth_state":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OAuth state",
            )
        next_path = payload.get("next") or "/dashboard"
        # Only accept same-origin relative paths; reject absolute URLs
        # so we can't be used as an open redirect.
        if not isinstance(next_path, str) or not next_path.startswith("/"):
            next_path = "/dashboard"
        return next_path

    def google_authorize_url(self, next_path: str = "/dashboard") -> str:
        if not settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google sign-in is not configured",
            )
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": self._google_redirect_uri(),
            "response_type": "code",
            "scope": GOOGLE_LOGIN_SCOPES,
            "state": self._mint_oauth_state(next_path),
            "access_type": "online",
            "prompt": "select_account",
            "include_granted_scopes": "true",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def google_exchange(self, code: str, state: str) -> tuple[User, str, str]:
        """Validate state, exchange code for tokens, fetch userinfo,
        find-or-create the User, and mint a Fuse JWT.

        Returns ``(user, fuse_jwt, next_path)``.
        """
        next_path = self._verify_oauth_state(state)
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google sign-in is not configured",
            )

        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self._google_redirect_uri(),
                },
            )
            token_data = token_resp.json()
            if "error" in token_data or "access_token" not in token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Google token exchange failed: "
                        f"{token_data.get('error_description') or token_data.get('error') or 'unknown'}"
                    ),
                )

            userinfo_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            if userinfo_resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google userinfo fetch failed",
                )
            info = userinfo_resp.json()

        email = info.get("email")
        if not email or not info.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account has no verified email",
            )
        full_name = info.get("name") or None
        avatar_url = info.get("picture") or None

        user = await self.user_repo.get_by_email(email)
        if user is None:
            user = User(
                email=email,
                hashed_password=None,
                auth_provider="google",
                full_name=full_name,
                avatar_url=avatar_url,
            )
            self.db.add(user)
            await self.db.flush()
            await WorkspaceService(self.db).create_personal_workspace(user)
            await self.db.refresh(user)
        else:
            # Backfill missing profile data for existing email-registered
            # users who sign in with Google for the first time — keep
            # whatever they already set so we never clobber a custom
            # display name or avatar.
            changed = False
            if user.full_name is None and full_name:
                user.full_name = full_name
                changed = True
            if user.avatar_url is None and avatar_url:
                user.avatar_url = avatar_url
                changed = True
            if changed:
                await self.user_repo.update(user)

        access_token = self.create_access_token(data={"sub": user.email})
        return user, access_token, next_path

    async def forgot_password(self, email: str) -> bool:
        user = await self.user_repo.get_by_email(email)
        if not user:
            # For security, we return True even if user doesn't exist
            # to prevent email enumeration.
            return True

        # 15-minute single-use reset token. The `type` claim is asserted
        # in reset_password() so a regular login JWT can't impersonate
        # a reset link.
        reset_token = self.create_access_token(
            data={"sub": user.email, "type": "password_reset"},
            expires_delta=timedelta(minutes=RESET_TOKEN_EXPIRES_MINUTES),
        )

        # Build the absolute URL from settings.FRONTEND_URL so prod
        # emails point at the production frontend, not localhost.
        reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={reset_token}"

        await self.email_service.send_password_reset(
            PasswordResetEmail(
                to_email=user.email,
                reset_url=reset_url,
                expires_minutes=RESET_TOKEN_EXPIRES_MINUTES,
            )
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
