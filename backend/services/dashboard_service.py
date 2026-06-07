from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.models.models import User, Candidate, Job, Application, Department
from backend.utils.cache import cached

class DashboardService:
    @cached(ttl_seconds=300)
    async def get_dashboard_summary(self, db: AsyncSession) -> dict:
        """
        Computes dashboard aggregate stats. Cached in Redis for 5 minutes.
        """
        # Execute parallel count queries
        users_query = select(func.count(User.id))
        candidates_query = select(func.count(Candidate.id))
        jobs_query = select(func.count(Job.id))
        apps_query = select(func.count(Application.id))
        depts_query = select(func.count(Department.id))

        users_result = await db.execute(users_query)
        candidates_result = await db.execute(candidates_query)
        jobs_result = await db.execute(jobs_query)
        apps_result = await db.execute(apps_query)
        depts_result = await db.execute(depts_query)

        return {
            "total_users": users_result.scalar() or 0,
            "total_candidates": candidates_result.scalar() or 0,
            "total_jobs": jobs_result.scalar() or 0,
            "total_applications": apps_result.scalar() or 0,
            "total_departments": depts_result.scalar() or 0
        }
