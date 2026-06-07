from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_async_db
from backend.api.deps import get_current_active_admin
from backend.services.onboarding_service import OnboardingService
from backend.services.sendgrid_email_service import SendGridEmailService
from backend.models.models import User, Job, Candidate, Application
from sqlalchemy import select
from backend.services.sendgrid_email_service import SendGridEmailService, get_interview_invite_template, get_hired_template
from backend.models.models import User, Job, Candidate, Application
from sqlalchemy import select

# Initialize email service
email_service = SendGridEmailService()
router = APIRouter(prefix="/admin/onboarding", tags=["Onboarding"])
service = OnboardingService()


@router.post('/candidate/{candidate_id}')
async def onboard_candidate(candidate_id: int, department_id: int = None, background_tasks: BackgroundTasks = None, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_admin)):
    try:
        # run onboarding and send email in background
        def _job():
            import asyncio
            async def _run():
                async with db.bind.connect() as conn:
                    pass
            asyncio.run(_run())

        # perform onboard synchronously but email is sent inside service; wrap in background if desired
        result = await service.onboard_candidate(db, candidate_id, department_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
