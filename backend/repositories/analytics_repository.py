from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from backend.models.models import (
    Application,
    Job,
    Candidate,
    Employee,
    Department,
    InterviewSchedule,
    Attendance,
    LeaveRequest,
    PerformanceReview,
    KPI,
    User,
)


class AnalyticsRepository:
    async def get_total_employees(self, db: AsyncSession) -> int:
        query = select(func.count(Employee.id))
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def get_active_employees(self, db: AsyncSession) -> int:
        query = select(func.count(Employee.id)).join(User, Employee.user_id == User.id).where(User.is_active == True)
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def get_total_candidates(self, db: AsyncSession) -> int:
        query = select(func.count(Candidate.id))
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def get_active_jobs(self, db: AsyncSession) -> int:
        query = select(func.count(Job.id)).where(Job.status == 'Open')
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def get_total_departments(self, db: AsyncSession) -> int:
        query = select(func.count(Department.id))
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def get_new_hires_this_month(self, db: AsyncSession) -> int:
        query = select(func.count(Employee.id)).where(func.date_trunc('month', Employee.joining_date) == func.date_trunc('month', func.now()))
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def get_employee_growth_rate(self, db: AsyncSession) -> float:
        # simple month-over-month growth rate
        current = select(func.count(Employee.id)).where(func.date_trunc('month', Employee.joining_date) == func.date_trunc('month', func.now()))
        prev = select(func.count(Employee.id)).where(func.date_trunc('month', Employee.joining_date) == func.date_trunc('month', func.now() - text("interval '1 month'")))
        cur = (await db.execute(current)).scalar() or 0
        prv = (await db.execute(prev)).scalar() or 0
        if prv == 0:
            return float(cur)
        return float((cur - prv) / prv)

    # Recruitment metrics
    async def get_applications_per_job(self, db: AsyncSession) -> List[Dict[str, Any]]:
        query = (
            select(Job.title, func.count(Application.id).label('count'))
            .outerjoin(Application, Job.id == Application.job_id)
            .group_by(Job.title)
            .order_by(func.count(Application.id).desc())
        )
        result = await db.execute(query)
        return [{'job_title': row.title, 'applications_count': row.count} for row in result.all()]

    async def get_hiring_funnel(self, db: AsyncSession) -> Dict[str, int]:
        total_app = (await db.execute(select(func.count(Application.id)))).scalar() or 0
        shortlisted = (await db.execute(select(func.count(Application.id)).where(Application.application_status.ilike('%shortlist%')))).scalar() or 0
        interviewed = (await db.execute(select(func.count(InterviewSchedule.id)))).scalar() or 0
        hired = (await db.execute(select(func.count(Application.id)).where(Application.application_status.ilike('%hired%')))).scalar() or 0
        return {'applied': int(total_app), 'shortlisted': int(shortlisted), 'interviewed': int(interviewed), 'hired': int(hired)}

    async def get_interview_success_rate(self, db: AsyncSession) -> float:
        interviewed = (await db.execute(select(func.count(InterviewSchedule.id)))).scalar() or 0
        hired = (await db.execute(select(func.count(Application.id)).where(Application.application_status.ilike('%hired%')))).scalar() or 0
        if interviewed == 0:
            return 0.0
        return float(hired) / float(interviewed)

    async def get_shortlisted_vs_rejected(self, db: AsyncSession) -> Dict[str, int]:
        shortlisted = (await db.execute(select(func.count(Application.id)).where(Application.application_status.ilike('%shortlist%')))).scalar() or 0
        rejected = (await db.execute(select(func.count(Application.id)).where(Application.application_status.ilike('%reject%')))).scalar() or 0
        return {'shortlisted': int(shortlisted), 'rejected': int(rejected)}

    async def get_average_time_to_hire(self, db: AsyncSession) -> float:
        # approximate: average days between application.applied_at and interview_schedules.created_at
        query = select(func.avg(func.date_part('day', func.age(InterviewSchedule.created_at, Application.applied_at))))
        query = query.select_from(Application).join(InterviewSchedule, InterviewSchedule.application_id == Application.id)
        res = await db.execute(query)
        val = res.scalar()
        return float(val) if val is not None else 0.0

    async def get_monthly_recruitment_trends(self, db: AsyncSession) -> List[Dict[str, Any]]:
        query = (
            select(func.date_trunc('month', Application.applied_at).label('month'), func.count(Application.id).label('count'))
            .group_by(func.date_trunc('month', Application.applied_at))
            .order_by(func.date_trunc('month', Application.applied_at))
        )
        result = await db.execute(query)
        return [{'month': row.month.isoformat() if row.month else None, 'applications': row.count} for row in result.all()]

    # Attendance metrics
    async def get_attendance_percentage(self, db: AsyncSession) -> float:
        total_days = (await db.execute(select(func.count(Attendance.id)))).scalar() or 0
        present_days = (await db.execute(select(func.count(Attendance.id)).where(Attendance.check_in != None))).scalar() or 0
        if total_days == 0:
            return 0.0
        return float(present_days) / float(total_days) * 100.0

    async def get_monthly_attendance_trends(self, db: AsyncSession) -> List[Dict[str, Any]]:
        query = (
            select(func.date_trunc('month', Attendance.date).label('month'), func.count(Attendance.id).label('count'))
            .group_by(func.date_trunc('month', Attendance.date))
            .order_by(func.date_trunc('month', Attendance.date))
        )
        result = await db.execute(query)
        return [{'month': row.month.isoformat() if row.month else None, 'attendance_count': row.count} for row in result.all()]

    async def get_department_attendance_comparison(self, db: AsyncSession) -> List[Dict[str, Any]]:
        query = (
            select(Department.department_name, func.count(Attendance.id).label('count'))
            .join(Employee, Employee.department_id == Department.id)
            .join(Attendance, Attendance.employee_id == Employee.id)
            .group_by(Department.department_name)
            .order_by(func.count(Attendance.id).desc())
        )
        result = await db.execute(query)
        return [{'department': row.department_name, 'attendance_count': row.count} for row in result.all()]

    # Leave metrics
    async def get_leave_requests_count(self, db: AsyncSession) -> int:
        query = select(func.count(LeaveRequest.id))
        result = await db.execute(query)
        return int(result.scalar() or 0)

    async def get_leave_approval_rate(self, db: AsyncSession) -> float:
        total = (await db.execute(select(func.count(LeaveRequest.id)))).scalar() or 0
        approved = (await db.execute(select(func.count(LeaveRequest.id)).where(LeaveRequest.status.ilike('%approve%')))).scalar() or 0
        if total == 0:
            return 0.0
        return float(approved) / float(total)

    async def get_department_leave_stats(self, db: AsyncSession) -> List[Dict[str, Any]]:
        query = (
            select(Department.department_name, func.count(LeaveRequest.id).label('count'))
            .join(Employee, Employee.department_id == Department.id)
            .join(LeaveRequest, LeaveRequest.employee_id == Employee.id)
            .group_by(Department.department_name)
            .order_by(func.count(LeaveRequest.id).desc())
        )
        result = await db.execute(query)
        return [{'department': row.department_name, 'leave_count': row.count} for row in result.all()]

    # Performance metrics
    async def get_top_performing_employees(self, db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
        query = (
            select(Employee.id, User.name, func.avg(PerformanceReview.score).label('avg_score'))
            .join(User, Employee.user_id == User.id)
            .join(PerformanceReview, PerformanceReview.employee_id == Employee.id)
            .group_by(Employee.id, User.name)
            .order_by(func.avg(PerformanceReview.score).desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return [{'employee_id': row.id, 'name': row.name, 'avg_score': float(row.avg_score)} for row in result.all()]

    async def get_top_performing_departments(self, db: AsyncSession) -> List[Dict[str, Any]]:
        query = (
            select(Department.department_name, func.avg(PerformanceReview.score).label('avg_score'))
            .join(Employee, Employee.department_id == Department.id)
            .join(PerformanceReview, PerformanceReview.employee_id == Employee.id)
            .group_by(Department.department_name)
            .order_by(func.avg(PerformanceReview.score).desc())
        )
        result = await db.execute(query)
        return [{'department': row.department_name, 'avg_score': float(row.avg_score)} for row in result.all()]

    async def get_average_performance_rating(self, db: AsyncSession) -> float:
        query = select(func.avg(PerformanceReview.score))
        result = await db.execute(query)
        val = result.scalar()
        return float(val) if val is not None else 0.0

