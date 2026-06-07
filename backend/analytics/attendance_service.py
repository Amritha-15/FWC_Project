from datetime import timedelta, date
from typing import List, Dict
from sqlalchemy import select, func, cast, Date
from backend.models.models import Attendance

class AttendanceAnalyticsService:
    async def get_attendance_trends(self, db) -> List[Dict[str, object]]:
        query = (
            select(
                Attendance.attendance_date.label('label'),
                func.count(Attendance.id).label('value')
            )
            .group_by(Attendance.attendance_date)
            .order_by(Attendance.attendance_date.asc())
            .limit(30)
        )
        result = await db.execute(query)
        return [
            {"label": row.label.strftime('%Y-%m-%d'), "value": int(row.value)}
            for row in result.fetchall()
        ]

    async def get_attendance_percentage(self, db) -> List[Dict[str, object]]:
        total_query = select(func.count(Attendance.id).label('total'))
        present_query = select(func.count(Attendance.id).label('present')).where(Attendance.check_in != None)

        total = (await db.execute(total_query)).scalar() or 0
        present = (await db.execute(present_query)).scalar() or 0
        absent = total - present
        return [
            {"name": "Present", "value": int(present)},
            {"name": "Absent", "value": int(absent)}
        ]

    async def get_employee_attendance_summary(self, db, employee_id: int) -> List[Dict[str, object]]:
        query = (
            select(
                Attendance.attendance_date.label('label'),
                Attendance.working_hours.label('value')
            )
            .where(Attendance.employee_id == employee_id)
            .order_by(Attendance.attendance_date.asc())
            .limit(30)
        )
        result = await db.execute(query)
        return [
            {"label": row.label.strftime('%Y-%m-%d'), "value": float(row.value or 0)}
            for row in result.fetchall()
        ]
