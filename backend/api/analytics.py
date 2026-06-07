from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_async_db
from backend.api.deps import get_current_active_admin
from backend.schemas.schemas import AnalyticsDashboardResponse
from backend.services.analytics_service import AnalyticsService
from backend.models.models import User

router = APIRouter(prefix="/admin/analytics", tags=["Analytics"])
analytics_service = AnalyticsService()

@router.get("", response_model=AnalyticsDashboardResponse)
async def get_analytics_metrics(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Exposes chart-friendly recruitment and department metrics. Cached in Redis.
    """
    return await analytics_service.get_analytics_dashboard(db)


@router.get('/attendance')
async def get_attendance_metrics(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    return await analytics_service.get_attendance_metrics(db)


@router.get('/leave')
async def get_leave_metrics(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    return await analytics_service.get_leave_metrics(db)


@router.get('/performance')
async def get_performance_metrics(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    return await analytics_service.get_performance_metrics(db)


@router.get('/kpis')
async def get_kpi_metrics(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    return await analytics_service.get_kpi_metrics(db)
