from typing import List, Dict
from sqlalchemy import select, func
from backend.models.models import PerformanceReview, Employee

class PerformanceAnalyticsService:
    async def get_employee_performance_trend(self, db, employee_id: int) -> List[Dict[str, object]]:
        query = (
            select(PerformanceReview.score.label('value'), PerformanceReview.created_at.label('label'))
            .where(PerformanceReview.employee_id == employee_id)
            .order_by(PerformanceReview.created_at.asc())
            .limit(30)
        )
        result = await db.execute(query)
        return [{"label": row.label.strftime('%Y-%m-%d'), "value": float(row.value or 0)} for row in result.fetchall()]

    async def get_team_performance_comparison(self, db) -> List[Dict[str, object]]:
        query = (
            select(Employee.department_id, func.avg(PerformanceReview.score).label('value'))
            .join(PerformanceReview, Employee.id == PerformanceReview.employee_id)
            .group_by(Employee.department_id)
        )
        result = await db.execute(query)
        return [{"name": str(row.department_id), "value": float(row.value or 0)} for row in result.fetchall()]
