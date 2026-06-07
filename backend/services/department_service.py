from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from backend.repositories.department_repository import DepartmentRepository
from backend.schemas.schemas import DepartmentCreate
from backend.models.models import Department
from backend.utils.cache import clear_cache_pattern

class DepartmentService:
    def __init__(self):
        self.dept_repo = DepartmentRepository()

    async def create_department(self, db: AsyncSession, dept_in: DepartmentCreate) -> Department:
        existing_dept = await self.dept_repo.get_by_name(db, dept_in.department_name)
        if existing_dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department name already exists."
            )
        obj_in = {
            "department_name": dept_in.department_name,
            "description": dept_in.description
        }
        dept = await self.dept_repo.create(db, obj_in=obj_in)
        clear_cache_pattern("*dashboard*")
        clear_cache_pattern("*list_departments*")
        return dept

    async def list_departments(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Department]:
        return await self.dept_repo.list_departments(db, skip=skip, limit=limit)

    async def update_department(self, db: AsyncSession, dept_id: int, dept_in: DepartmentCreate) -> Department:
        db_obj = await self.dept_repo.get(db, dept_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found."
            )
        
        # Check if new name matches another department
        existing_dept = await self.dept_repo.get_by_name(db, dept_in.department_name)
        if existing_dept and existing_dept.id != dept_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another department already has this name."
            )

        obj_in = {
            "department_name": dept_in.department_name,
            "description": dept_in.description
        }
        dept = await self.dept_repo.update(db, db_obj=db_obj, obj_in=obj_in)
        clear_cache_pattern("*dashboard*")
        clear_cache_pattern("*list_departments*")
        return dept

    async def delete_department(self, db: AsyncSession, dept_id: int) -> Department:
        dept = await self.dept_repo.remove(db, id=dept_id)
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found."
            )
        clear_cache_pattern("*dashboard*")
        clear_cache_pattern("*list_departments*")
        return dept
