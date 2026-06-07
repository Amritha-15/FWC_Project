from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.analytics_repository import AnalyticsRepository
from backend.utils.cache import cached
from backend.analytics.attendance_service import AttendanceAnalyticsService
from backend.analytics.leave_service import LeaveAnalyticsService
from backend.analytics.performance_service import PerformanceAnalyticsService
from backend.analytics.kpi_service import KPIAnalyticsService

class AnalyticsService:
    def __init__(self):
        self.analytics_repo = AnalyticsRepository()
        self.attendance_service = AttendanceAnalyticsService()
        self.leave_service = LeaveAnalyticsService()
        self.performance_service = PerformanceAnalyticsService()
        self.kpi_service = KPIAnalyticsService()

    @cached(ttl_seconds=300)
    async def get_analytics_dashboard(self, db: AsyncSession) -> dict:
        """
        Retrieves all chart analytics statistics in parallel. Cached in Redis for 5 minutes.
        """
        apps_per_job = await self.analytics_repo.get_applications_per_job(db)
        candidate_status = await self.analytics_repo.get_candidate_status_breakdown(db)
        employees_per_dept = await self.analytics_repo.get_employees_per_department(db)
        recruitment_summary = await self.analytics_repo.get_recruitment_summary(db)

        return {
            "applications_per_job": apps_per_job,
            "candidate_status_breakdown": candidate_status,
            "employees_per_department": employees_per_dept,
            "recruitment_summary": recruitment_summary
        }

    async def get_attendance_metrics(self, db: AsyncSession):
        return {
            "attendance_trends": await self.attendance_service.get_attendance_trends(db),
            "attendance_percentage": await self.attendance_service.get_attendance_percentage(db)
        }

    async def get_leave_metrics(self, db: AsyncSession):
        return {
            "leave_breakdown": await self.leave_service.get_leave_breakdown(db),
            "leave_trends": await self.leave_service.get_leave_trends(db)
        }

    async def get_performance_metrics(self, db: AsyncSession):
        return {
            "team_performance_comparison": await self.performance_service.get_team_performance_comparison(db)
        }

    async def get_kpi_metrics(self, db: AsyncSession):
        return {
            "kpi_summary": await self.kpi_service.get_kpi_summary(db),
            "kpi_history": await self.kpi_service.get_kpi_history(db)
        }
