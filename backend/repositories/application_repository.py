from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.models import Application


class ApplicationRepository:
    async def create(self, db: AsyncSession, obj_in: dict) -> Application:
        db_obj = Application(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def list_for_candidate(self, db: AsyncSession, candidate_id: int, skip: int = 0, limit: int = 50) -> List[Application]:
        q = select(Application).where(Application.candidate_id == candidate_id).order_by(Application.applied_at.desc()).offset(skip).limit(limit)
        res = await db.execute(q)
        return res.scalars().all()

    async def get(self, db: AsyncSession, application_id: int):
        q = select(Application).where(Application.id == application_id)
        res = await db.execute(q)
        return res.scalars().first()

    async def list_for_job(self, db: AsyncSession, job_id: int, skip: int = 0, limit: int = 100):
        q = select(Application).where(Application.job_id == job_id).order_by(Application.applied_at.desc()).offset(skip).limit(limit)
        res = await db.execute(q)
        return res.scalars().all()

    async def update(self, db: AsyncSession, db_obj: Application, obj_in: dict) -> Application:
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
