from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.database.session import get_async_db
from backend.api.deps import get_current_active_admin
from backend.schemas.schemas import UserCreate, UserResponse, RoleUpdateRequest
from backend.services.user_service import UserService
from backend.models.models import User

router = APIRouter(prefix="/admin/users", tags=["User Management"])
user_service = UserService()

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    CRUD Endpoint: Create a new user (Candidate, Manager, HR, Employee, or Admin).
    """
    return await user_service.create_user(db, user_in)

@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    CRUD Endpoint: Paginated listing of users.
    """
    return await user_service.list_users(db, skip=skip, limit=limit)

@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_in: RoleUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    CRUD Endpoint: Update role (admin, hr, candidate, manager, employee).
    """
    return await user_service.update_role(db, user_id, role_in.role)

@router.put("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    CRUD Endpoint: Deactivate a user profile.
    """
    return await user_service.deactivate_user(db, user_id)
