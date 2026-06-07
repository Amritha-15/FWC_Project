from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select
import traceback
import asyncio 

from backend.database.session import (
    get_async_db,
    async_session_maker,
)

from backend.models.models import Job as JobModel

from backend.services.ai_service import (
    process_resume,
    evaluate_and_store_interview,
    run_skill_gap,
)

router = APIRouter(prefix="/api/ai", tags=["AI"])


# ------------------------------------------------------------------
# Request Models
# ------------------------------------------------------------------

class ResumeProcessRequest(BaseModel):
    candidate_id: int
    application_id: Optional[int] = None
    job_id: Optional[int] = None
    resume_text: Optional[str] = ""


class InterviewEvalRequest(BaseModel):
    application_id: int
    transcript: List[Dict[str, str]]


class SkillGapRequest(BaseModel):
    candidate_skills: str
    required_skills: str
    transcript: List[Dict[str, str]] = []


# ------------------------------------------------------------------
# Resume Processing
# ------------------------------------------------------------------

@router.post("/process-resume")
async def api_process_resume(
    req: ResumeProcessRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Process a single candidate resume using Resume Agent.
    """

    result = await process_resume(
        db=db,
        candidate_id=req.candidate_id,
        application_id=req.application_id,
        resume_text=req.resume_text,
        job_id=req.job_id,
    )

    return result


# ------------------------------------------------------------------
# Screen Single Job
# ------------------------------------------------------------------

@router.post("/screen-job/{job_id}")
async def api_screen_job(
    job_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Screen all applications for one job.
    Uses Resume Agent only.
    """

    from backend.services.ai_service import screen_job

    result = await screen_job(db, job_id)

    if result.get("error"):
        raise HTTPException(
            status_code=404,
            detail=result["error"],
        )

    return result


# ------------------------------------------------------------------
# Background Screening
# ------------------------------------------------------------------

@router.post("/screen-job/{job_id}/run")
async def api_screen_job_run(
    job_id: int,
    background_tasks: BackgroundTasks,
):

    from backend.services.ai_service import screen_job

    async def worker(job_id: int):

        async with async_session_maker() as session:

            try:

                print(f"Starting Resume Screening Job {job_id}")

                await screen_job(session, job_id)

                print(f"Finished Resume Screening Job {job_id}")

            except Exception:

                traceback.print_exc()

    background_tasks.add_task(worker, job_id)

    return {
        "success": True,
        "message": "Resume screening started",
        "job_id": job_id,
    }


# ------------------------------------------------------------------
# Screen All Open Jobs
# ------------------------------------------------------------------

@router.post("/screen-all")
async def api_screen_all(db: AsyncSession = Depends(get_async_db)):
    print("🔥 HIT: screen-all endpoint")
    from backend.services.ai_service import screen_job

    print("=== screen-all called ===")

    # Fetch all Open job IDs using the injected session
    result = await db.execute(
        sa_select(JobModel.id).where(JobModel.status == "Open")
    )
    job_ids = [row[0] for row in result.fetchall()]
    print(f"=== Open jobs found: {job_ids} ===")

    if not job_ids:
        return {
            "success": True,
            "message": "No open jobs found",
            "jobs_processed": 0,
            "jobs_failed": {},
        }

    # Each job gets its own isolated session
    async def screen_one(job_id: int):
        print(f"=== Screening job {job_id} ===")
        try:
            from backend.database.session import async_session_maker as maker
            async with maker() as job_session:
                res = await screen_job(job_session, job_id)
                print(f"=== Job {job_id} done ===")
                return res
        except Exception as e:
            traceback.print_exc()
            return {"job_id": job_id, "error": str(e)}

    results = await asyncio.gather(*[screen_one(jid) for jid in job_ids])

    successes = [r for r in results if not r.get("error")]
    failures = {r.get("job_id", "?"): r["error"] for r in results if r.get("error")}

    print(f"=== screen-all done: {len(successes)} succeeded, {failures} failed ===")

    return {
        "success": True,
        "message": "Resume screening completed",
        "jobs_processed": len(successes),
        "jobs_failed": failures,
    }


# ------------------------------------------------------------------
# Generate Interview Questions  (called by candidate AIInterview.tsx)
# ------------------------------------------------------------------

class GenerateQuestionsRequest(BaseModel):
    application_id: int


@router.post("/generate-questions")
async def api_generate_questions(
    req: GenerateQuestionsRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Fetch candidate + job from DB for the given application_id and
    return 3 personalised interview questions via the LLM.
    """
    from backend.services.ai_service import generate_interview_questions

    result = await generate_interview_questions(db, req.application_id)

    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return result


# ------------------------------------------------------------------
# Transcribe Audio  (called by candidate AIInterview.tsx – voice mode)
# ------------------------------------------------------------------

from fastapi import UploadFile, File
import tempfile, os


@router.post("/transcribe")
async def api_transcribe(audio: UploadFile = File(...)):
    """
    Accept an audio file, send to Groq Whisper, return transcript text.
    """
    from backend.services.ai_service import transcribe_audio

    audio_bytes = await audio.read()

    # Write to a named temp file so Groq client can read it
    suffix = os.path.splitext(audio.filename or "audio.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = await transcribe_audio(tmp_path)
    finally:
        os.unlink(tmp_path)

    return result


@router.post("/evaluate-interview")
async def api_evaluate_interview(
    req: InterviewEvalRequest,
    db: AsyncSession = Depends(get_async_db),
):

    return await evaluate_and_store_interview(
        db,
        req.application_id,
        req.transcript,
    )


# ------------------------------------------------------------------
# Skill Gap Analysis
# ------------------------------------------------------------------

@router.post("/skill-gap")
async def api_skill_gap(req: SkillGapRequest):

    return await run_skill_gap(
        req.candidate_skills,
        req.required_skills,
        req.transcript,
    )