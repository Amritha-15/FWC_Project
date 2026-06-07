from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.models.models import Department
from backend.repositories.base import BaseRepository

class DepartmentRepository(BaseRepository[Department]):
    def __init__(self):
        super().__init__(Department)

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Department]:
        result = await db.execute(select(Department).filter(Department.department_name == name))
        return result.scalars().first()

    async def list_departments(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Department]:
        result = await db.execute(select(Department).order_by(Department.id.desc()).offset(skip).limit(limit))
        return result.scalars().all()
