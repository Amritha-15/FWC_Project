from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_async_db
from backend.api.deps import get_current_active_hr, get_current_active_manager
from backend.services.interview_service import InterviewService
from backend.services.email_service import EmailService
from backend.repositories.interview_repository import InterviewRepository
import shutil, os

router = APIRouter(prefix="/interviews", tags=["Interviews"])
service = InterviewService()
emailer = EmailService()
repo = InterviewRepository()

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'interviews'))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post('/upload')
async def upload_interview(
    file: UploadFile = File(...),
    candidate_id: int = Form(None),
    job_id: int = Form(None),
    application_id: int = Form(None),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_async_db)
):
    try:
        dest = os.path.join(UPLOAD_DIR, file.filename)
        with open(dest, 'wb') as f:
            shutil.copyfileobj(file.file, f)

        # Transcribe and evaluate in background using an async session
        from backend.database.session import async_session_maker

        def _worker(path, cand_id, j_id, app_id):
            import asyncio
            async def _run():
                # create an async session for background work
                async with async_session_maker() as session:
                    transcript_text = await service.transcribe_file(path)
                    transcript = [{'question': '', 'answer': t} for t in transcript_text.split('\n') if t.strip()]
                    try:
                        await service.evaluate_transcript(session, cand_id, j_id, app_id, transcript)
                    except Exception:
                        pass
            asyncio.run(_run())

        if background_tasks:
            background_tasks.add_task(_worker, dest, candidate_id, job_id, application_id)

        return {"detail": "file uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
*** End Patch