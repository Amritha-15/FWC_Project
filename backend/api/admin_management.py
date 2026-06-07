from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_async_db
from backend.api.deps import get_current_active_admin
from backend.services.admin_service import AdminService
from backend.models.models import User

router = APIRouter(prefix="/admin/management", tags=["AdminManagement"])
admin_service = AdminService()


class RoleUpdateRequest(BaseModel):
    role: str


@router.get("/overview")
async def company_overview(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin),
):
    """Company-wide aggregated overview for Admins only."""
    return await admin_service.get_company_overview(db)


@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin),
):
    return await admin_service.list_users(db, skip=skip, limit=limit)


@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    payload: RoleUpdateRequest,
    db: AsyncSession = Depends(get_async_db),
    request: Request = None,
    current_user: User = Depends(get_current_active_admin),
):
    # capture old state for audit
    old_user = await admin_service.user_repo.get(db, user_id)
    user = await admin_service.update_user_role(db, user_id, payload.role)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # create audit log
    ip = request.client.host if request and request.client else None
    await admin_service.log_action(db, admin_id=current_user.id, action=f"update_role to {payload.role}", target_user_id=user_id, old_value=str(getattr(old_user, 'role', None)), new_value=payload.role, ip_address=ip)
    return {"detail": "role updated"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
    request: Request = None,
    current_user: User = Depends(get_current_active_admin),
):
    old_user = await admin_service.user_repo.get(db, user_id)
    user = await admin_service.deactivate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    ip = request.client.host if request and request.client else None
    await admin_service.log_action(db, admin_id=current_user.id, action="deactivate_user", target_user_id=user_id, old_value=str(getattr(old_user, 'is_active', None)), new_value=str(False), ip_address=ip)
    return {"detail": "user deactivated"}
