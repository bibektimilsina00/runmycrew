from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

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


# ── Google sign-in ────────────────────────────────────────────────────
#
# Two-step browser redirect, NOT an API call from the SPA:
#   1. `/auth/google/start?next=/foo` → 302 to Google consent screen.
#      `next` is signed into the state JWT so we can come back to the
#      same path after auth.
#   2. Google → `/auth/google/callback?code=...&state=...` → backend
#      exchanges the code, find-or-creates the User, mints a RunMyCrew JWT,
#      and 302s to `FRONTEND_URL/login?token=...&next=...`. The login
#      page consumes the token query and hydrates the auth store.
#
# We use a redirect (vs. setting an HttpOnly cookie) on purpose: the
# rest of the product reads the JWT from localStorage via Zustand, and
# threading a brand-new cookie-auth path through every API call would
# be a much larger refactor. Token-in-URL is fine here because it's
# stripped from the URL bar on the very next render in Login.tsx.


def _login_redirect_url(token: str, next_path: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    qs = urlencode({"token": token, "next": next_path})
    return f"{base}/login?{qs}"


def _login_error_url(error: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    qs = urlencode({"error": error})
    return f"{base}/login?{qs}"


@router.get("/google/start")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def google_start(
    request: Request,
    next: str = Query(default="/dashboard"),
    service: AuthService = Depends(get_auth_service),
):
    url = service.google_authorize_url(next_path=next)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/google/callback")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def google_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    service: AuthService = Depends(get_auth_service),
):
    # User clicked "Cancel" on the consent screen, or Google bounced us.
    if error or not code or not state:
        return RedirectResponse(
            url=_login_error_url(error or "google_cancelled"),
            status_code=status.HTTP_302_FOUND,
        )
    try:
        _user, token, next_path = await service.google_exchange(code=code, state=state)
    except HTTPException as exc:
        return RedirectResponse(
            url=_login_error_url(str(exc.detail) or "google_failed"),
            status_code=status.HTTP_302_FOUND,
        )
    return RedirectResponse(
        url=_login_redirect_url(token, next_path),
        status_code=status.HTTP_302_FOUND,
    )


# ── GitHub sign-in ────────────────────────────────────────────────────


@router.get("/github/start")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def github_start(
    request: Request,
    next: str = Query(default="/dashboard"),
    service: AuthService = Depends(get_auth_service),
):
    url = service.github_authorize_url(next_path=next)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/github/callback")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def github_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    service: AuthService = Depends(get_auth_service),
):
    if error or not code or not state:
        return RedirectResponse(
            url=_login_error_url(error or "github_cancelled"),
            status_code=status.HTTP_302_FOUND,
        )
    try:
        _user, token, next_path = await service.github_exchange(code=code, state=state)
    except HTTPException as exc:
        return RedirectResponse(
            url=_login_error_url(str(exc.detail) or "github_failed"),
            status_code=status.HTTP_302_FOUND,
        )
    return RedirectResponse(
        url=_login_redirect_url(token, next_path),
        status_code=status.HTTP_302_FOUND,
    )


# ── Microsoft sign-in ─────────────────────────────────────────────────


@router.get("/microsoft/start")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def microsoft_start(
    request: Request,
    next: str = Query(default="/dashboard"),
    service: AuthService = Depends(get_auth_service),
):
    url = service.microsoft_authorize_url(next_path=next)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/microsoft/callback")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def microsoft_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    service: AuthService = Depends(get_auth_service),
):
    if error or not code or not state:
        return RedirectResponse(
            url=_login_error_url(error or "microsoft_cancelled"),
            status_code=status.HTTP_302_FOUND,
        )
    try:
        _user, token, next_path = await service.microsoft_exchange(code=code, state=state)
    except HTTPException as exc:
        return RedirectResponse(
            url=_login_error_url(str(exc.detail) or "microsoft_failed"),
            status_code=status.HTTP_302_FOUND,
        )
    return RedirectResponse(
        url=_login_redirect_url(token, next_path),
        status_code=status.HTTP_302_FOUND,
    )
