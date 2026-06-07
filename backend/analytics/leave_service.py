from typing import List, Dict
from sqlalchemy import select, func
from backend.models.models import LeaveRequest

class LeaveAnalyticsService:
    async def get_leave_breakdown(self, db) -> List[Dict[str, object]]:
        query = (
            select(LeaveRequest.status, func.count(LeaveRequest.id).label('value'))
            .group_by(LeaveRequest.status)
        )
        result = await db.execute(query)
        return [{"name": row.status or 'Unknown', "value": int(row.value)} for row in result.fetchall()]

    async def get_leave_trends(self, db) -> List[Dict[str, object]]:
        query = (
            select(LeaveRequest.start_date.label('label'), func.count(LeaveRequest.id).label('value'))
            .group_by(LeaveRequest.start_date)
            .order_by(LeaveRequest.start_date.asc())
            .limit(30)
        )
        result = await db.execute(query)
        return [{"label": row.label.strftime('%Y-%m-%d'), "value": int(row.value)} for row in result.fetchall()]
