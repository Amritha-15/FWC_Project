from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import AuditLog


class AuditRepository:
    async def create_log(self, db: AsyncSession, *, admin_id: int | None, action: str, target_user_id: int | None = None, old_value: str | None = None, new_value: str | None = None, ip_address: str | None = None):
        log = AuditLog(
            admin_id=admin_id,
            action=action,
            target_user_id=target_user_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log
