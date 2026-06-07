from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.models import User
from backend.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def list_users(self, db: AsyncSession, *, skip: int = 0, limit: int = 10) -> List[User]:
        result = await db.execute(select(User).order_by(User.id.desc()).offset(skip).limit(limit))
        return result.scalars().all()

    async def update_role(self, db: AsyncSession, user_id: int, role: str) -> Optional[User]:
        user = await self.get(db, user_id)
        if user:
            user.role = role
            await db.commit()
            await db.refresh(user)
        return user

    async def deactivate_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        user = await self.get(db, user_id)
        if user:
            user.is_active = False
            await db.commit()
            await db.refresh(user)
        return user
