from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_async_db
from backend.api.deps import get_current_active_admin
from backend.schemas.schemas import DashboardSummaryResponse
from backend.services.dashboard_service import DashboardService
from backend.models.models import User

router = APIRouter(prefix="/admin/dashboard", tags=["Dashboard"])
dashboard_service = DashboardService()

@router.get("", response_model=DashboardSummaryResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Exposes Admin dashboard statistics aggregates. Protected by RBAC JWT.
    """
    return await dashboard_service.get_dashboard_summary(db)
