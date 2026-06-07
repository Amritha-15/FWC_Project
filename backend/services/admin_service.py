from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.analytics_service import AnalyticsService
from backend.repositories.user_repository import UserRepository
from backend.repositories.audit_repository import AuditRepository
from backend.repositories.analytics_repository import AnalyticsRepository


class AdminService:
    def __init__(self):
        self.analytics = AnalyticsService()
        self.user_repo = UserRepository()
        self.audit_repo = AuditRepository()
        self.analytics_repo = AnalyticsRepository()

    async def get_company_overview(self, db: AsyncSession) -> dict:
        # Company metrics
        total_employees = await self.analytics_repo.get_total_employees(db)
        active_employees = await self.analytics_repo.get_active_employees(db)
        total_candidates = await self.analytics_repo.get_total_candidates(db)
        active_jobs = await self.analytics_repo.get_active_jobs(db)
        total_departments = await self.analytics_repo.get_total_departments(db)
        new_hires_month = await self.analytics_repo.get_new_hires_this_month(db)
        employee_growth = await self.analytics_repo.get_employee_growth_rate(db)

        # Recruitment metrics
        apps_per_job = await self.analytics_repo.get_applications_per_job(db)
        hiring_funnel = await self.analytics_repo.get_hiring_funnel(db)
        interview_success = await self.analytics_repo.get_interview_success_rate(db)
        shortlist_reject = await self.analytics_repo.get_shortlisted_vs_rejected(db)
        avg_time_to_hire = await self.analytics_repo.get_average_time_to_hire(db)
        monthly_recruitment = await self.analytics_repo.get_monthly_recruitment_trends(db)

        # Attendance & leave & performance
        attendance_percentage = await self.analytics_repo.get_attendance_percentage(db)
        monthly_attendance = await self.analytics_repo.get_monthly_attendance_trends(db)
        dept_attendance = await self.analytics_repo.get_department_attendance_comparison(db)

        leave_requests = await self.analytics_repo.get_leave_requests_count(db)
        leave_approval_rate = await self.analytics_repo.get_leave_approval_rate(db)
        dept_leave = await self.analytics_repo.get_department_leave_stats(db)

        top_employees = await self.analytics_repo.get_top_performing_employees(db)
        top_departments = await self.analytics_repo.get_top_performing_departments(db)
        avg_perf = await self.analytics_repo.get_average_performance_rating(db)

        return {
            "company": {
                "total_employees": total_employees,
                "active_employees": active_employees,
                "total_candidates": total_candidates,
                "active_jobs": active_jobs,
                "total_departments": total_departments,
                "new_hires_this_month": new_hires_month,
                "employee_growth_rate": employee_growth,
            },
            "recruitment": {
                "applications_per_job": apps_per_job,
                "hiring_funnel": hiring_funnel,
                "interview_success_rate": interview_success,
                "shortlisted_vs_rejected": shortlist_reject,
                "average_time_to_hire_days": avg_time_to_hire,
                "monthly_recruitment_trends": monthly_recruitment,
            },
            "attendance": {
                "attendance_percentage": attendance_percentage,
                "monthly_trends": monthly_attendance,
                "department_comparison": dept_attendance,
            },
            "leave": {
                "total_requests": leave_requests,
                "approval_rate": leave_approval_rate,
                "department_stats": dept_leave,
            },
            "performance": {
                "top_employees": top_employees,
                "top_departments": top_departments,
                "average_rating": avg_perf,
            }
        }

    async def list_users(self, db: AsyncSession, skip: int = 0, limit: int = 50) -> List[dict]:
        users = await self.user_repo.list_users(db, skip=skip, limit=limit)
        # return lightweight dicts
        return [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]

    async def update_user_role(self, db: AsyncSession, user_id: int, role: str):
        old_user = await self.user_repo.get(db, user_id)
        updated = await self.user_repo.update_role(db, user_id, role)
        # audit log will be created by caller with admin context
        return updated

    async def deactivate_user(self, db: AsyncSession, user_id: int):
        old_user = await self.user_repo.get(db, user_id)
        updated = await self.user_repo.deactivate_user(db, user_id)
        # audit log will be created by caller with admin context
        return updated

    async def log_action(self, db: AsyncSession, *, admin_id: int | None, action: str, target_user_id: int | None = None, old_value: str | None = None, new_value: str | None = None, ip_address: str | None = None):
        return await self.audit_repo.create_log(db, admin_id=admin_id, action=action, target_user_id=target_user_id, old_value=old_value, new_value=new_value, ip_address=ip_address)
