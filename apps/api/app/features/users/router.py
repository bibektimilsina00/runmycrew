from fastapi import APIRouter, Depends

from apps.api.app.features.auth.schemas import UserOut
from apps.api.app.features.users.models import User
from apps.api.app.features.users.schemas import UserUpdate
from apps.api.app.features.users.service import UserService, get_user_service
from apps.api.app.shared.dependencies import get_current_user

router = APIRouter()


@router.put("/me", response_model=UserOut)
async def update_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """Update profile information of the currently authenticated user."""
    return await service.update_me(current_user, user_in)
