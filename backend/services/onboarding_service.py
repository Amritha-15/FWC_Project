import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import Candidate, Employee, Onboarding, User
from backend.repositories.user_repository import UserRepository
from backend.services.sendgrid_email_service import SendGridEmailService
from backend.core.security import get_password_hash


class OnboardingService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.emailer = SendGridEmailService()

    async def onboard_candidate(self, db: AsyncSession, candidate_id: int, department_id: int = None, role: str = 'employee'):
        # fetch candidate and user
        stmt = Candidate.__table__.select().where(Candidate.__table__.c.id == candidate_id)
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            raise ValueError('Candidate not found')
        candidate = dict(row)
        user_id = candidate.get('user_id')

        # load user
        user = await self.user_repo.get(db, user_id)
        if not user:
            raise ValueError('Associated user not found')

        # generate temporary password
        temp_password = secrets.token_urlsafe(10)
        user.password_hash = get_password_hash(temp_password)
        user.role = role
        user.is_active = True
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # create employee record
        emp = Employee(
            user_id=user.id,
            employee_code=f"EMP{user.id:05d}",
            department_id=department_id,
            designation='New Hire'
        )
        db.add(emp)
        await db.commit()
        await db.refresh(emp)

        # onboarding record
        ob = Onboarding(candidate_id=candidate_id, employee_id=emp.id, offer_letter_status='Sent', joining_status='Onboarded')
        db.add(ob)
        # update candidate status
        await db.execute(Candidate.__table__.update().where(Candidate.__table__.c.id == candidate_id).values(current_status='Onboarded'))
        await db.commit()

        # send welcome email (sync) - caller should call in background
        subject = 'Welcome to the company'
        html = f"<p>Hi {user.name},</p><p>Your employee account has been created. Temporary password: <b>{temp_password}</b></p>"
        try:
            self.emailer.send_email(to_email=user.email, to_name=user.name, subject=subject, html_content=html)
        except Exception:
            pass

        return {'employee_id': emp.id, 'temp_password': temp_password}
