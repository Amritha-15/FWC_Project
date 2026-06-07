from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr
from backend.api.deps import get_current_active_admin
from backend.services.sendgrid_email_service import SendGridEmailService

router = APIRouter(prefix="/admin/email", tags=["Email"])
emailer = SendGridEmailService()


class TestEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str


@router.post('/send-test')
async def send_test_email(payload: TestEmailRequest, background_tasks: BackgroundTasks, current_user=Depends(get_current_active_admin)):
    try:
        # schedule send in background to avoid blocking
        background_tasks.add_task(emailer.send_simple, payload.to, payload.subject, payload.body, True)
        return {"detail": "Test email scheduled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
