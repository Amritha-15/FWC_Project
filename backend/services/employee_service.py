from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from backend.models.models import Employee, Attendance, LeaveRequest
from backend.repositories.user_repository import UserRepository
from datetime import date, datetime
from backend.core.security import get_password_hash, verify_password
from backend.repositories.notification_repository import NotificationRepository
from backend.models.models import PerformanceReview

class EmployeeService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.notification_repo = NotificationRepository()

    async def _get_employee_id(self, db: AsyncSession, user):
        stmt = select(Employee).where(Employee.user_id == user.id)
        result = await db.execute(stmt)
        employee = result.scalars().first()
        if not employee:
            employee = Employee(
                user_id=user.id,
                employee_code=f"EMP{user.id}",
                designation="Employee"
            )
            db.add(employee)
            await db.commit()
            await db.refresh(employee)
        return employee.id

    async def check_in(self, db: AsyncSession, user):
        employee_id = await self._get_employee_id(db, user)
        today = date.today()
        q = Attendance.__table__.insert().values(employee_id=employee_id, check_in=datetime.utcnow(), attendance_date=today)
        await db.execute(q)
        return {"message": "Checked in"}

    async def check_out(self, db: AsyncSession, user):
        employee_id = await self._get_employee_id(db, user)
        today = date.today()
        stmt = select(Attendance).where(
            Attendance.__table__.c.employee_id == employee_id,
            Attendance.__table__.c.attendance_date == today,
            Attendance.__table__.c.check_out == None
        )
        result = await db.execute(stmt)
        attendance = result.scalars().first()
        if not attendance:
            raise ValueError('No open attendance record found for today')

        attendance.check_out = datetime.utcnow()
        if attendance.check_in:
            attendance.working_hours = round((attendance.check_out - attendance.check_in).total_seconds() / 3600, 2)
        db.add(attendance)
        return {"message": "Checked out", "working_hours": float(attendance.working_hours or 0)}

    async def get_attendance_history(self, db: AsyncSession, user):
        employee_id = await self._get_employee_id(db, user)
        q = Attendance.__table__.select().where(Attendance.__table__.c.employee_id == employee_id).order_by(Attendance.__table__.c.attendance_date.desc())
        res = await db.execute(q)
        rows = res.fetchall()
        return [dict(r._mapping) for r in rows]

    async def get_profile(self, db: AsyncSession, user):
        # return user + employee info
        u = await self.user_repo.get(db, user.id)
        emp = None
        
        stmt = select(Employee).where(Employee.user_id == user.id)
        res = await db.execute(stmt)
        employee_record = res.scalars().first()
        
        if employee_record:
            emp = {
                'employee_id': employee_record.id,
                'designation': employee_record.designation,
                'department_id': employee_record.department_id,
                'employee_code': employee_record.employee_code,
                'joining_date': employee_record.joining_date.isoformat() if employee_record.joining_date else None,
            }
        return {
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'profile_picture': u.profile_picture,
            'role': u.role,
            'employee': emp,
        }

    async def update_profile(self, db: AsyncSession, user, payload: dict):
        u = await self.user_repo.get(db, user.id)
        u.name = payload.get('name', u.name)
        u.profile_picture = payload.get('profile_picture', u.profile_picture)
        db.add(u)
        await db.commit()
        await db.refresh(u)
        return {'detail': 'profile updated'}

    async def change_password(self, db: AsyncSession, user, old_password: str, new_password: str):
        u = await self.user_repo.get(db, user.id)
        if not verify_password(old_password, u.password_hash):
            raise ValueError('Old password does not match')
        u.password_hash = get_password_hash(new_password)
        db.add(u)
        await db.commit()
        return {'detail': 'password changed'}

    async def get_performance_reviews(self, db: AsyncSession, user):
        employee_id = await self._get_employee_id(db, user)
        q = PerformanceReview.__table__.select().where(PerformanceReview.__table__.c.employee_id == employee_id).order_by(PerformanceReview.__table__.c.created_at.desc())
        res = await db.execute(q)
        return [dict(r._mapping) for r in res.fetchall()]

    async def get_leave_balance(self, db: AsyncSession, user):
        # naive calculation: total leaves allowed - approved leaves taken
        # For now, assume annual entitlement = 18
        entitlement = 18
        employee_id = await self._get_employee_id(db, user)
        taken = (await db.execute(select(func.count(LeaveRequest.id)).where(LeaveRequest.__table__.c.employee_id == employee_id, LeaveRequest.__table__.c.status.ilike('%approved%')))).scalar() or 0
        return {'entitlement': entitlement, 'taken': int(taken), 'available': entitlement - int(taken)}

    async def list_notifications(self, db: AsyncSession, user, skip: int = 0, limit: int = 50):
        notifications = await self.notification_repo.list_for_user(db, user.id, skip=skip, limit=limit)
        return [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ]

    async def mark_notification_read(self, db: AsyncSession, notification_id: int):
        await self.notification_repo.mark_read(db, notification_id)
        return {'detail': 'marked read'}

    async def apply_leave(self, db: AsyncSession, user, payload: dict):
        employee_id = await self._get_employee_id(db, user)
        start = payload.get('start_date')
        end = payload.get('end_date')
        reason = payload.get('reason')
        leave_type = payload.get('leave_type', 'General')
        if not start or not end:
            raise ValueError('start_date and end_date required')
        q = LeaveRequest.__table__.insert().values(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            reason=reason,
            status='Pending'
        )
        await db.execute(q)
        return {"message": "Leave applied"}

    async def get_my_leaves(self, db: AsyncSession, user):
        employee_id = await self._get_employee_id(db, user)
        q = LeaveRequest.__table__.select().where(LeaveRequest.__table__.c.employee_id == employee_id).order_by(LeaveRequest.__table__.c.created_at.desc())
        res = await db.execute(q)
        rows = res.fetchall()
        return [dict(r._mapping) for r in rows]
