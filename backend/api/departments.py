from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.database.session import get_async_db
from backend.api.deps import get_current_active_admin
from backend.schemas.schemas import DepartmentCreate, DepartmentResponse
from backend.services.department_service import DepartmentService
from backend.models.models import User

router = APIRouter(prefix="/admin/departments", tags=["Department Management"])
dept_service = DepartmentService()

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_in: DepartmentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    CRUD Endpoint: Create a new department.
    """
    return await dept_service.create_department(db, dept_in)

@router.get("", response_model=List[DepartmentResponse])
async def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    CRUD Endpoint: List departments.
    """
    return await dept_service.list_departments(db, skip=skip, limit=limit)

@router.put("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: int,
    dept_in: DepartmentCreate,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    CRUD Endpoint: Update details of a department.
    """
    return await dept_service.update_department(db, dept_id, dept_in)

@router.delete("/{dept_id}", response_model=DepartmentResponse)
async def delete_department(
    dept_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    CRUD Endpoint: Delete a department.
    """
    return await dept_service.delete_department(db, dept_id)
