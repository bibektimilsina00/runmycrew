from fastapi import APIRouter, Depends, HTTPException, Request, status

from apps.api.app.core.config import settings
from apps.api.app.features.auth.schemas import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
)
from apps.api.app.features.auth.service import AuthService, get_auth_service
from apps.api.app.features.users.models import User
from apps.api.app.middleware.rate_limit import limiter
from apps.api.app.shared.dependencies import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserOut)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(
    request: Request, user_in: UserRegister, service: AuthService = Depends(get_auth_service)
):
    return await service.register(user_in)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request, user_login: UserLogin, service: AuthService = Depends(get_auth_service)
):
    user = await service.authenticate(user_login)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = service.create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def forgot_password(
    request: Request, body: ForgotPasswordRequest, service: AuthService = Depends(get_auth_service)
):
    await service.forgot_password(body.email)
    return MessageResponse(message="If your account exists, a password reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def reset_password(
    request: Request, body: ResetPasswordRequest, service: AuthService = Depends(get_auth_service)
):
    await service.reset_password(body.token, body.new_password)
    return MessageResponse(message="Password has been successfully reset.")
