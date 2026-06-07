from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from backend.repositories.user_repository import UserRepository
from backend.schemas.schemas import UserCreate
from backend.models.models import User
from backend.core.security import get_password_hash
from backend.utils.cache import clear_cache_pattern
from backend.websocket.manager import ws_manager

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        # Check if email is already taken
        existing_user = await self.user_repo.get_by_email(db, user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered."
            )

        # Hash the password
        hashed_password = get_password_hash(user_in.password)
        obj_in = {
            "name": user_in.name,
            "email": user_in.email,
            "password_hash": hashed_password,
            "role": user_in.role,
            "is_active": True
        }

        user = await self.user_repo.create(db, obj_in=obj_in)
        
        # Clear dashboard stats and user list cache on modification
        clear_cache_pattern("*dashboard*")
        clear_cache_pattern("*list_users*")

        # Broadcast NEW_EMPLOYEE_ONBOARDED if user is employee
        if user_in.role in ["employee", "manager"]:
            await ws_manager.broadcast("NEW_EMPLOYEE_ONBOARDED", {
                "user_id": user.id,
                "name": user.name,
                "role": user.role,
                "email": user.email
            })

        return user

    async def list_users(self, db: AsyncSession, skip: int = 0, limit: int = 10) -> List[User]:
        return await self.user_repo.list_users(db, skip=skip, limit=limit)

    async def update_role(self, db: AsyncSession, user_id: int, role: str) -> User:
        user = await self.user_repo.update_role(db, user_id, role)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        clear_cache_pattern("*dashboard*")
        clear_cache_pattern("*list_users*")
        return user

    async def deactivate_user(self, db: AsyncSession, user_id: int) -> User:
        user = await self.user_repo.deactivate_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found."
            )
        clear_cache_pattern("*dashboard*")
        clear_cache_pattern("*list_users*")
        return user
