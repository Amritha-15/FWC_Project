from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.repositories.base import BaseRepository
from backend.models.models import Candidate


class CandidateRepository(BaseRepository[Candidate]):
    def __init__(self):
        super().__init__(Candidate)

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> Optional[Candidate]:
        result = await db.execute(select(Candidate).filter(Candidate.user_id == user_id))
        return result.scalars().first()
