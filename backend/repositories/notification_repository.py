from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.models import Notification

class NotificationRepository:
    async def list_for_user(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 50):
        q = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        res = await db.execute(q)
        return res.scalars().all()

    async def mark_read(self, db: AsyncSession, notification_id: int):
        q = Notification.__table__.update().where(Notification.__table__.c.id == notification_id).values(is_read=True)
        await db.execute(q)
        return True
