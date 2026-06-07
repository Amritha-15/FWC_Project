from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.models import Job


class JobRepository:
    async def list_open(self, db: AsyncSession, skip: int = 0, limit: int = 50) -> List[Job]:
        q = select(Job).where(Job.status == 'Open').order_by(Job.created_at.desc()).offset(skip).limit(limit)
        res = await db.execute(q)
        return res.scalars().all()

    async def get(self, db: AsyncSession, job_id: int):
        q = select(Job).where(Job.id == job_id)
        res = await db.execute(q)
        return res.scalars().first()
