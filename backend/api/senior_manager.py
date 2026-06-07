from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_async_db
from backend.api.deps import get_current_active_manager
from backend.services.senior_manager_service import SeniorManagerService
from fastapi import Request

router = APIRouter(prefix="/senior-manager", tags=["SeniorManager"])
service = SeniorManagerService()


@router.get('/team-dashboard')
async def team_dashboard(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.get_team_dashboard(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/team-members')
async def team_members(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.get_team_members(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/team-members/{employee_id}')
async def team_member_details(employee_id: int, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.get_team_member_details(db, current_user, employee_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/performance/history/{employee_id}')
async def performance_history(employee_id: int, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.get_performance_history(db, current_user, employee_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/performance/{review_id}')
async def edit_performance(review_id: int, payload: dict, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.edit_performance_review(db, current_user, review_id, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/leave-history/{employee_id}')
async def leave_history(employee_id: int, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.get_leave_history_for_member(db, current_user, employee_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/team-productivity')
async def team_productivity(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.team_productivity_analytics(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/top-performers')
async def top_performers(limit: int = 10, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.get_top_performers(db, current_user, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/team-attendance')
async def team_attendance(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.get_team_attendance(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/leaves/pending')
async def pending_leaves(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.get_pending_leaves(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/leaves/{leave_id}/approve')
async def approve_leave(leave_id: int, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.approve_leave(db, current_user, leave_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/leaves/{leave_id}/reject')
async def reject_leave(leave_id: int, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.reject_leave(db, current_user, leave_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/performance/review')
async def submit_review(payload: dict, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.submit_performance_review(db, current_user, payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/kpis')
async def kpi_summary(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_manager)):
    try:
        return await service.get_kpi_summary(db, current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
