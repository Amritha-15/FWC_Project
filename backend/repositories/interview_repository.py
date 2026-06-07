from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import text
from backend.models.models import InterviewResult


class InterviewRepository:
    async def create_result(self, db: AsyncSession, payload: dict):
        # Insert only columns that exist in the current DB table schema to avoid
        # failing when the DB is out-of-sync with the models.
        table_cols = set(InterviewResult.__table__.c.keys())
        filtered = {k: v for k, v in payload.items() if k in table_cols}

        insert_stmt = InterviewResult.__table__.insert().values(**filtered).returning(InterviewResult.__table__.c.id)
        res = await db.execute(insert_stmt)
        new_id = res.scalar()
        await db.commit()

        # Return ORM instance if possible
        obj = await db.get(InterviewResult, new_id)
        return obj

    async def get_by_application(self, db: AsyncSession, application_id: int):
        res = await db.execute(InterviewResult.__table__.select().where(InterviewResult.__table__.c.application_id == application_id))
        return res.fetchone()
