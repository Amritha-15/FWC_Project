from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_async_db
from backend.api.deps import get_current_active_employee
from backend.services.employee_service import EmployeeService
from backend.schemas.schemas import LeaveApplicationRequest
from fastapi import Request
from backend.schemas.schemas import UpdateProfileRequest, ChangePasswordRequest

router = APIRouter(prefix="/employee", tags=["Employee"])
service = EmployeeService()


@router.post('/check-in')
async def check_in(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    """Employee check-in"""
    try:
        result = await service.check_in(db, current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/check-out')
async def check_out(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    """Employee check-out"""
    try:
        result = await service.check_out(db, current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/attendance')
async def attendance_history(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        data = await service.get_attendance_history(db, current_user)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/profile')
async def get_profile(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        return await service.get_profile(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/profile')
async def update_profile(payload: UpdateProfileRequest, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        return await service.update_profile(db, current_user, payload.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/change-password')
async def change_password(payload: ChangePasswordRequest, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        return await service.change_password(db, current_user, payload.old_password, payload.new_password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/reviews')
async def my_reviews(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        return await service.get_performance_reviews(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/leave/balance')
async def leave_balance(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        return await service.get_leave_balance(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/notifications')
async def my_notifications(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        return await service.list_notifications(db, current_user, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/notifications/{notification_id}/read')
async def mark_notification_read(notification_id: int, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        return await service.mark_notification_read(db, notification_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/leave')
async def apply_leave(payload: LeaveApplicationRequest, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        res = await service.apply_leave(db, current_user, payload.dict())
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/leave')
async def my_leaves(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_employee)):
    try:
        res = await service.get_my_leaves(db, current_user)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
