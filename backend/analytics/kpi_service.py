from typing import List, Dict
from sqlalchemy import select
from backend.models.models import KPI

class KPIAnalyticsService:
    async def get_kpi_summary(self, db) -> List[Dict[str, object]]:
        query = (
            select(KPI.team.label('name'), KPI.value.label('value'))
            .order_by(KPI.recorded_at.desc())
            .limit(50)
        )
        result = await db.execute(query)
        return [{"name": row.name, "value": float(row.value)} for row in result.fetchall()]

    async def get_kpi_history(self, db) -> List[Dict[str, object]]:
        query = (
            select(KPI.metric.label('label'), KPI.value.label('value'))
            .order_by(KPI.recorded_at.asc())
            .limit(50)
        )
        result = await db.execute(query)
        return [{"label": row.label, "value": float(row.value)} for row in result.fetchall()]
