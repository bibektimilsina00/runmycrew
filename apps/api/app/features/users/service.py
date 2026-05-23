from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.auth.service import AuthService
from apps.api.app.features.users.models import User
from apps.api.app.features.users.repository import UserRepository
from apps.api.app.features.users.schemas import UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)
        self.auth_service = AuthService(db)

    async def update_me(self, current_user: User, user_in: UserUpdate) -> User:
        if user_in.full_name is not None:
            current_user.full_name = user_in.full_name.strip() or None

        if user_in.password is not None:
            current_user.hashed_password = self.auth_service.get_password_hash(user_in.password)

        return await self.repository.update(current_user)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)
