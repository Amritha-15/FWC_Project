from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import LeaveRequest, Attendance, PerformanceReview, KPI
from sqlalchemy import select, func, text
from backend.models.models import Employee, User


class SeniorManagerService:
    def __init__(self):
        pass

    async def _get_manager_employee_id(self, db: AsyncSession, current_user) -> int:
        """Get or auto-create the Employee record for the current manager user."""
        stmt = select(Employee).where(Employee.user_id == current_user.id)
        result = await db.execute(stmt)
        emp = result.scalars().first()
        if not emp:
            emp = Employee(
                user_id=current_user.id,
                employee_code=f"MGR{current_user.id}",
                designation="Manager"
            )
            db.add(emp)
            await db.commit()
            await db.refresh(emp)
        return emp.id

    async def get_team_dashboard(self, db: AsyncSession, current_user):
        q = text("SELECT COUNT(*) as total_leaves FROM leave_requests WHERE status='Pending'")
        res = await db.execute(q)
        total_leaves = res.scalar() or 0
        return {"pending_leaves": total_leaves}

    async def get_team_members(self, db: AsyncSession, current_user):
        manager_emp_id = await self._get_manager_employee_id(db, current_user)

        query = (
            select(Employee.id, Employee.employee_code, Employee.designation, User.id.label('user_id'), User.name, User.email)
            .join(User, Employee.user_id == User.id)
            .where(Employee.manager_id == manager_emp_id)
        )
        res = await db.execute(query)
        return [dict(r._mapping) for r in res.fetchall()]

    async def get_team_member_details(self, db: AsyncSession, current_user, employee_id: int):
        query = (
            select(Employee, User).join(User, Employee.user_id == User.id).where(Employee.id == employee_id)
        )
        res = await db.execute(query)
        row = res.first()
        if not row:
            return None
        emp, user = row
        return {
            'employee': {
                'id': emp.id,
                'employee_code': emp.employee_code,
                'designation': emp.designation,
                'department_id': emp.department_id,
                'joining_date': emp.joining_date.isoformat() if emp.joining_date else None,
            },
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            }
        }

    async def get_performance_history(self, db: AsyncSession, current_user, employee_id: int):
        q = PerformanceReview.__table__.select().where(PerformanceReview.__table__.c.employee_id == employee_id).order_by(PerformanceReview.__table__.c.created_at.desc())
        res = await db.execute(q)
        return [dict(r._mapping) for r in res.fetchall()]

    async def edit_performance_review(self, db: AsyncSession, current_user, review_id: int, payload: dict):
        stmt = PerformanceReview.__table__.select().where(PerformanceReview.__table__.c.id == review_id)
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            raise ValueError('Review not found')
        existing = dict(row._mapping)
        upd = PerformanceReview.__table__.update().where(PerformanceReview.__table__.c.id == review_id).values(
            score=payload.get('score', existing.get('score')),
            feedback=payload.get('feedback', existing.get('feedback'))
        )
        await db.execute(upd)
        return {'detail': 'review updated'}

    async def get_leave_history_for_member(self, db: AsyncSession, current_user, employee_id: int):
        q = LeaveRequest.__table__.select().where(LeaveRequest.__table__.c.employee_id == employee_id).order_by(LeaveRequest.__table__.c.created_at.desc())
        res = await db.execute(q)
        return [dict(r._mapping) for r in res.fetchall()]

    async def team_productivity_analytics(self, db: AsyncSession, current_user):
        manager_emp_id = await self._get_manager_employee_id(db, current_user)

        q_hours = text("""
            SELECT AVG(a.working_hours) as avg_hours
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE e.manager_id = :mgr
        """)
        res = await db.execute(q_hours, {'mgr': manager_emp_id})
        avg_hours = res.scalar() or 0

        q_perf = select(func.avg(PerformanceReview.score)).select_from(
            PerformanceReview.__table__.join(Employee, Employee.id == PerformanceReview.__table__.c.employee_id)
        ).where(Employee.manager_id == manager_emp_id)
        avg_perf = (await db.execute(q_perf)).scalar() or 0

        return {'avg_work_hours': float(avg_hours), 'avg_performance': float(avg_perf)}

    async def get_top_performers(self, db: AsyncSession, current_user, limit: int = 10):
        manager_emp_id = await self._get_manager_employee_id(db, current_user)

        query = (
            select(Employee.id, User.name, func.avg(PerformanceReview.score).label('avg_score'))
            .join(User, Employee.user_id == User.id)
            .join(PerformanceReview, PerformanceReview.employee_id == Employee.id)
            .where(Employee.manager_id == manager_emp_id)
            .group_by(Employee.id, User.name)
            .order_by(func.avg(PerformanceReview.score).desc())
            .limit(limit)
        )
        try:
            res = await db.execute(query)
            return [{'employee_id': r.id, 'name': r.name, 'rating': float(r.avg_score)} for r in res.fetchall()]
        except Exception as e:
            # If the performance_reviews table or score column is missing, return empty list
            return []

    async def get_team_attendance(self, db: AsyncSession, current_user):
        q = text("""
            SELECT attendance_date, COUNT(*) as present
            FROM attendance
            GROUP BY attendance_date
            ORDER BY attendance_date DESC
            LIMIT 7
        """)
        res = await db.execute(q)
        rows = res.fetchall()
        present_pct = 90
        if rows:
            total = sum(r[1] for r in rows)
            present_pct = min(round((total / (len(rows) * max(total, 1))) * 100, 1), 100)
        return {'present_pct': present_pct, 'late_pct': 5, 'absent_pct': max(0, 100 - present_pct - 5)}

    async def get_pending_leaves(self, db: AsyncSession, current_user):
        q = text("""
            SELECT lr.id, lr.employee_id, u.name as employee_name,
                   lr.start_date, lr.end_date, lr.reason, lr.status
            FROM leave_requests lr
            JOIN employees e ON lr.employee_id = e.id
            JOIN users u ON e.user_id = u.id
            WHERE lr.status = 'Pending'
            ORDER BY lr.created_at DESC
        """)
        res = await db.execute(q)
        return [dict(r._mapping) for r in res.fetchall()]

    async def approve_leave(self, db: AsyncSession, current_user, leave_id: int):
        stmt = LeaveRequest.__table__.update().where(LeaveRequest.__table__.c.id == leave_id).values(
            status='Approved', approved_by=current_user.id
        )
        await db.execute(stmt)
        await db.commit()
        return {"message": "Leave approved"}

    async def reject_leave(self, db: AsyncSession, current_user, leave_id: int):
        stmt = LeaveRequest.__table__.update().where(LeaveRequest.__table__.c.id == leave_id).values(status='Rejected')
        await db.execute(stmt)
        await db.commit()
        return {"message": "Leave rejected"}

    async def submit_performance_review(self, db: AsyncSession, current_user, payload: dict):
        emp_id = payload.get('employee_id')
        # Accept both 'rating' (from frontend) and 'score' (internal)
        score = payload.get('rating') or payload.get('score')
        feedback = payload.get('feedback')
        await db.execute(
            PerformanceReview.__table__.insert().values(
                employee_id=emp_id,
                reviewer_id=current_user.id,
                score=score,
                feedback=feedback
            )
        )
        await db.commit()
        return {"message": "Review submitted"}

    async def get_kpi_summary(self, db: AsyncSession, current_user):
        q = KPI.__table__.select().order_by(KPI.__table__.c.recorded_at.desc()).limit(50)
        try:
            res = await db.execute(q)
            return [dict(r._mapping) for r in res.fetchall()]
        except Exception as e:
            # If the KPI table does not exist (e.g., missing migration), return empty list
            return []
