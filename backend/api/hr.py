"""
HR Backend API - FastAPI router exposing all HR actions on port 8080.

Covers:
  - Job management (CRUD)
  - Application management (list, detail, status update)
  - Interview scheduling
  - Interview results (per application / per candidate)
  - AI agent triggers (resume screening, candidate ranking,
    interview evaluation, skill-gap, hiring recommendation)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status, Body
from backend.repositories.job_repository import JobRepository
from backend.repositories.application_repository import ApplicationRepository
from backend.repositories.candidate_repository import CandidateRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from typing import Optional
from datetime import date, time
from collections import OrderedDict
import httpx

from backend.database.session import get_async_db
from backend.api.deps import get_current_active_hr
from backend.models.models import (
    Job, Application, Candidate, User,
    InterviewSchedule, InterviewResult, Notification
)
from backend.services.resume_parser import parse_resume
from backend.services.sendgrid_email_service import SendGridEmailService, get_interview_invite_template, get_hired_template
from backend.models.models import User, Job, Candidate, Application
from sqlalchemy import select

# Initialize SendGrid email service
email_service = SendGridEmailService()

router = APIRouter(prefix="/api/hr", tags=["HR Management"])
job_repo = JobRepository()
app_repo = ApplicationRepository()
cand_repo = CandidateRepository()

PYTHON_AI_URL = "http://localhost:8080"   # same FastAPI server – AI routes live at /api/agents/...


# ══════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════
async def _get_row(db, model, pk: int, label: str):
    result = await db.execute(select(model).where(model.id == pk))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return obj


# ══════════════════════════════════════════════════════════
#  1. JOB MANAGEMENT
# ══════════════════════════════════════════════════════════

# Duplicate dashboard_summary endpoint removed; using later definition.

async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    result = await db.execute(select(Job).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/jobs/{job_id}", summary="Get single job")
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    return await _get_row(db, Job, job_id, "Job")


@router.post("/jobs", status_code=status.HTTP_201_CREATED, summary="Create a new job posting")
async def create_job(
    body: dict,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    job = Job(
        title=body.get("title"),
        description=body.get("description"),
        required_skills=body.get("required_skills"),
        experience_required=body.get("experience_required"),
        department=body.get("department"),
        location=body.get("location"),
        salary_range=body.get("salary_range"),
        status=body.get("status", "Open"),
        created_by=current_user.id
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.put("/jobs/{job_id}", summary="Update a job posting")
async def update_job(
    job_id: int,
    body: dict,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    job = await _get_row(db, Job, job_id, "Job")
    allowed = ("title", "description", "required_skills", "experience_required",
               "department", "location", "salary_range", "status")
    for field in allowed:
        if field in body:
            setattr(job, field, body[field])
    await db.commit()
    await db.refresh(job)
    return job


@router.delete("/jobs/{job_id}", summary="Delete a job posting")
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    job = await _get_row(db, Job, job_id, "Job")
    await db.delete(job)
    await db.commit()
    return {"detail": f"Job {job_id} deleted"}


# ══════════════════════════════════════════════════════════
#  2. APPLICATION MANAGEMENT
# ══════════════════════════════════════════════════════════

@router.get("/applications", summary="List all applications (HR view)")
async def list_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    q = (
        select(
            Application.id,
            Application.application_status,
            Application.applied_at,
            Application.resume_score,
            Application.match_score,
            Application.ranking_position,
            Candidate.id.label("candidate_id"),
            User.name.label("candidate_name"),
            User.email.label("candidate_email"),
            Job.id.label("job_id"),
            Job.title.label("job_title"),
        )
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .offset(skip).limit(limit)
    )
    result = await db.execute(q)
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.get("/applications/{application_id}", summary="Get single application detail")
async def get_application(
    application_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    q = (
        select(
            Application,
            Candidate.id.label("candidate_id"),
            User.name.label("candidate_name"),
            User.email.label("candidate_email"),
            Job.title.label("job_title"),
            Job.required_skills.label("job_required_skills"),
        )
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    )
    result = await db.execute(q)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    app_obj = row[0]
    data = {c.name: getattr(app_obj, c.name) for c in Application.__table__.columns}
    data["candidate_name"] = row.candidate_name
    data["candidate_email"] = row.candidate_email
    data["job_title"] = row.job_title
    return data


@router.patch("/applications/{application_id}/status", summary="Update application status")
async def update_application_status(
    application_id: int,
    body: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    allowed_statuses = [
        "Applied", "Shortlisted", "Interview Approved",
        "Interview Scheduled", "Interview Completed",
        "Selected", "Rejected"
    ]
    new_status = body.get("status")
    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(allowed_statuses)}"
        )

    # Fetch application + candidate + job info in one query
    q = (
        select(Application, User.email.label("email"), User.name.label("name"),
               Job.title.label("job_title"), Candidate.id.label("cand_id"),
               User.id.label("user_id"))
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    )
    result = await db.execute(q)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    app_obj, email, name, job_title, cand_id, user_id = row

    # Update statuses
    app_obj.application_status = new_status
    await db.execute(
        update(Candidate).where(Candidate.id == cand_id).values(current_status=new_status)
    )

    # Create in-app notification
    notif = Notification(
        user_id=user_id,
        title=f"Application Status: {new_status}",
        message=f"Your application for {job_title} has been updated to: {new_status}."
    )
    db.add(notif)
    await db.commit()

    # Send email notification in background
    email_map = {
        "Shortlisted": ("Application Shortlisted",
                        f"<p>Congratulations <b>{name}</b>! Your application for <b>{job_title}</b> has been shortlisted.</p>"),
        "Interview Approved": ("Interview Approved",
                               f"<p>Hi <b>{name}</b>, your interview for <b>{job_title}</b> has been approved. We'll schedule it shortly.</p>"),
        "Interview Completed": ("Interview Completed",
                                f"<p>Hi <b>{name}</b>, thank you for completing the interview for <b>{job_title}</b>. We'll be in touch.</p>"),
        "Selected": ("Congratulations – You've Been Selected!",
                     f"<p>Dear <b>{name}</b>, we are thrilled to inform you that you have been <b>selected</b> for <b>{job_title}</b>. Our team will contact you with next steps.</p>"),
        "Rejected": ("Application Update",
                     f"<p>Dear <b>{name}</b>, we appreciate your interest in <b>{job_title}</b>. Unfortunately, your application was not selected at this time.</p>"),
    }
    if new_status in email_map:
        subject, html = email_map[new_status]
        # Log email dispatch attempt
        print(f"HR API: Scheduling email to {email} with subject '{subject}'")

    return {"detail": f"Status updated to '{new_status}'", "application_id": application_id}


# ══════════════════════════════════════════════════════════
#  3. INTERVIEW SCHEDULING
# ══════════════════════════════════════════════════════════

@router.post("/interviews/schedule", summary="Schedule an interview for a candidate")
async def schedule_interview(
    body: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    required = ["application_id", "interview_date", "interview_time"]
    for f in required:
        if not body.get(f):
            raise HTTPException(status_code=400, detail=f"'{f}' is required")

    application_id = body["application_id"]

    # Fetch application details
    q = (
        select(Application, Candidate.id.label("cand_id"),
               Job.id.label("job_id"), Job.title.label("job_title"),
               User.email.label("email"), User.name.label("name"),
               User.id.label("user_id"))
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    )
    result = await db.execute(q)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    app_obj, cand_id, job_id, job_title, email, name, user_id = row

    interview_date = date.fromisoformat(body["interview_date"])
    interview_time = time.fromisoformat(body["interview_time"])

    schedule = InterviewSchedule(
        candidate_id=cand_id,
        job_id=job_id,
        application_id=application_id,
        interview_date=interview_date,
        interview_time=interview_time,
        meeting_link=body.get("meeting_link"),
        notes=body.get("notes")
    )
    db.add(schedule)
    app_obj.application_status = "Interview Scheduled"
    await db.execute(
        update(Candidate).where(Candidate.id == cand_id).values(current_status="Interview Scheduled")
    )

    # In-app notification
    notif = Notification(
        user_id=user_id,
        title="Interview Scheduled",
        message=f"Your interview for {job_title} is on {interview_date} at {interview_time}. Link: {body.get('meeting_link', 'TBD')}"
    )
    db.add(notif)
    await db.commit()
    await db.refresh(schedule)

    # Email candidate
    subject = "Interview Scheduled"
    html = (
        f"<p>Dear <b>{name}</b>,</p>"
        f"<p>Your interview for <b>{job_title}</b> has been scheduled:<br>"
        f"📅 <b>Date:</b> {interview_date}<br>"
        f"⏰ <b>Time:</b> {interview_time}<br>"
        f"🔗 <b>Meeting Link:</b> {body.get('meeting_link', 'To be provided')}</p>"
        f"<p>Best of luck!</p>"
    )
    background_tasks.add_task(email_service.send_email, email, name, subject, html)

    return {"detail": "Interview scheduled", "schedule_id": schedule.id}


@router.get("/interviews", summary="List all scheduled interviews")
async def list_interviews(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    q = (
        select(
            InterviewSchedule.id,
            InterviewSchedule.interview_date,
            InterviewSchedule.interview_time,
            InterviewSchedule.meeting_link,
            InterviewSchedule.notes,
            InterviewSchedule.application_id,
            User.name.label("candidate_name"),
            User.email.label("candidate_email"),
            Job.title.label("job_title"),
        )
        .join(Candidate, InterviewSchedule.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, InterviewSchedule.job_id == Job.id)
        .order_by(InterviewSchedule.interview_date.desc())
    )
    result = await db.execute(q)
    return [dict(r) for r in result.mappings().all()]


# ══════════════════════════════════════════════════════════
#  4. INTERVIEW RESULTS (HR VIEW)
# ══════════════════════════════════════════════════════════

# Dashboard summary endpoint
@router.get("/dashboard/summary", summary="Dashboard aggregate stats")
async def dashboard_summary(db: AsyncSession = Depends(get_async_db)):
    """Return aggregated counts for users, candidates, jobs, applications, departments."""
    from backend.services.dashboard_service import DashboardService
    service = DashboardService()
    return await service.get_dashboard_summary(db)

# Jobs listing endpoint
@router.get("/jobs", summary="List all jobs")
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    q = select(Job).offset(skip).limit(limit)
    result = await db.execute(q)
    jobs = result.scalars().all()
    return jobs

@router.get("/interview-results", summary="List all interview evaluation results")
async def list_interview_results(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    # BUG FIX: use outerjoin instead of join so that any legacy rows that were
    # stored with NULL candidate_id / job_id (before the ai_service fix) are
    # still returned rather than silently dropped by the INNER JOIN.
    q = (
        select(
            InterviewResult.id,
            InterviewResult.application_id,
            InterviewResult.overall_score,
            InterviewResult.communication_score,
            InterviewResult.technical_score,
            InterviewResult.problem_solving_score,
            InterviewResult.confidence_score,
            InterviewResult.recommendation,
            InterviewResult.ai_feedback,
            InterviewResult.created_at,
            User.name.label("candidate_name"),
            Job.title.label("job_title"),
        )
        .outerjoin(Candidate, InterviewResult.candidate_id == Candidate.id)
        .outerjoin(User, Candidate.user_id == User.id)
        .outerjoin(Job, InterviewResult.job_id == Job.id)
        .order_by(InterviewResult.created_at.desc())
    )
    result = await db.execute(q)
    return [dict(r) for r in result.mappings().all()]


@router.get("/interview-results/{application_id}", summary="Get interview result for a specific application")
async def get_interview_result(
    application_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    q = (
        select(InterviewResult)
        .where(InterviewResult.application_id == application_id)
        .order_by(InterviewResult.created_at.desc())
    )
    result = await db.execute(q)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="No interview result found for this application")
    return row


# ══════════════════════════════════════════════════════════
#  5. AI AGENT TRIGGERS
# ══════════════════════════════════════════════════════════

@router.post("/agents/resume-screen/{candidate_id}", summary="Run AI resume screening agent")
async def run_resume_screen(
    candidate_id: int,
    request: dict = Body(None),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    # request may contain optional application_id, job_id, resume_text
    payload = {"candidate_id": candidate_id}
    if request:
        payload.update({k: request.get(k) for k in ["application_id", "job_id", "resume_text"] if request.get(k) is not None})
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{PYTHON_AI_URL}/api/ai/process-resume",
            json=payload
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


    async def run_candidate_ranking(
        job_id: int,
        request: dict = Body(None),
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(get_current_active_hr)
    ):
        # Build payload for AI ranking service
        payload: dict = {}
        if request:
            payload.update(request)
        # Ensure job_requirements are present
        if "job_requirements" not in payload:
            # fetch job details
            job = await job_repo.get(db, job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            payload["job_requirements"] = {
                "id": job.id,
                "title": job.title,
                "department": getattr(job, "department", None),
                "location": getattr(job, "location", None),
                "required_skills": getattr(job, "required_skills", None),
                "experience_required": getattr(job, "experience_required", None),
                "description": getattr(job, "description", None),
                "status": getattr(job, "status", None),
            }

    @router.post("/ai/screen-all", summary="Run AI screening for all jobs")
    async def screen_all(db: AsyncSession = Depends(get_async_db),
                         current_user=Depends(get_current_active_hr)):
        """Triggers AI screening across all jobs.
        Returns a mapping of job_id to screening results.
        """
        # Fetch all jobs
        jobs = await job_repo.list_all(db) if hasattr(job_repo, 'list_all') else []
        # If no helper, fallback to direct query
        if not jobs:
            result = await db.execute(select(Job))
            jobs = result.scalars().all()
        from backend.services.ai_service import screen_job
        all_results = {}
        for job in jobs:
            try:
                res = await screen_job(db, job.id)
                all_results[job.id] = res
            except Exception as e:
                all_results[job.id] = {"error": str(e)}
        return all_results

        # Ensure candidates list is present
        if "candidates" not in payload:
            applications = await app_repo.list_for_job(db, job_id)
            cand_list = []
            for app in applications:
                cand = await cand_repo.get(db, app.candidate_id)
                cand_list.append({
                    "candidate_id": cand.id if cand else None,
                    "application_id": app.id,
                    "resume_score": float(app.resume_score) if getattr(app, "resume_score", None) is not None else 0.0,
                })
            payload["candidates"] = cand_list
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{PYTHON_AI_URL}/api/ai/rank-candidates",
                json=payload
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()


@router.post("/agents/evaluate-interview/{application_id}", summary="Run AI interview evaluation agent")
async def run_interview_evaluation(
    application_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{PYTHON_AI_URL}/api/ai/evaluate-interview",
            json={"application_id": application_id}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@router.post("/agents/skill-gap/{application_id}", summary="Run AI skill-gap analysis agent")
async def run_skill_gap(
    application_id: int,
    request: dict = Body(None),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    # Build payload for skill-gap service
    payload: dict = {"application_id": application_id}
    if request:
        payload.update(request)
    # Ensure candidate_skills and required_skills are present (handle missing or null)
    if not payload.get("candidate_skills") or not payload.get("required_skills"):
        # Fetch application, candidate, and job details
        app = await app_repo.get(db, application_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        cand = await cand_repo.get(db, app.candidate_id)
        job = await job_repo.get(db, app.job_id)
        if not payload.get("candidate_skills"):
            payload["candidate_skills"] = str(getattr(cand, "skills", "")) or ""
        if not payload.get("required_skills"):
            payload["required_skills"] = str(getattr(job, "required_skills", "")) or ""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{PYTHON_AI_URL}/api/ai/skill-gap",
            json=payload
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@router.post("/agents/hiring-recommendation/{application_id}", summary="Run AI hiring recommendation agent")
async def run_hiring_recommendation(
    application_id: int,
    request: dict = Body(None),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    # Base payload includes the path parameter
    payload: dict = {"application_id": application_id}
    if request:
        payload.update(request)

    # Populate missing required fields from the Application record
    if not payload.get("resume_score") or not payload.get("candidate_ranking_score") or not payload.get("interview_score") or not payload.get("skill_gap_analysis"):
        app = await app_repo.get(db, application_id)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")
        payload.setdefault("resume_score", float(app.resume_score) if getattr(app, "resume_score", None) is not None else 0.0)
        payload.setdefault("candidate_ranking_score", int(app.ranking_position) if getattr(app, "ranking_position", None) is not None else 0)
        payload.setdefault("interview_score", float(app.interview_score) if getattr(app, "interview_score", None) is not None else 0.0)
        payload.setdefault("skill_gap_analysis", {})

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{PYTHON_AI_URL}/api/ai/recommend",
            json=payload,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


# ══════════════════════════════════════════════════════════
#  6. HR DASHBOARD SUMMARY
# ══════════════════════════════════════════════════════════

@router.get("/dashboard", summary="HR dashboard stats")
async def hr_dashboard(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    total_jobs         = (await db.execute(text("SELECT COUNT(*) FROM jobs"))).scalar()
    open_jobs          = (await db.execute(text("SELECT COUNT(*) FROM jobs WHERE status='Open'"))).scalar()
    total_apps         = (await db.execute(text("SELECT COUNT(*) FROM applications"))).scalar()
    shortlisted       = (await db.execute(text("SELECT COUNT(*) FROM applications WHERE application_status='Shortlisted'"))).scalar()
    interview_approved= (await db.execute(text("SELECT COUNT(*) FROM applications WHERE application_status='Interview Approved'"))).scalar()
    selected          = (await db.execute(text("SELECT COUNT(*) FROM applications WHERE application_status='Selected'"))).scalar()
    rejected          = (await db.execute(text("SELECT COUNT(*) FROM applications WHERE application_status='Rejected'"))).scalar()
    total_interviews  = (await db.execute(text("SELECT COUNT(*) FROM interview_schedules"))).scalar()
    evaluated         = (await db.execute(text("SELECT COUNT(*) FROM interview_results"))).scalar()

    return {
        "jobs": {"total": total_jobs, "open": open_jobs},
        "applications": {
            "total": total_apps,
            "shortlisted": shortlisted,
            "interview_approved": interview_approved,
            "selected": selected,
            "rejected": rejected,
        },
        "interviews": {"scheduled": total_interviews, "evaluated": evaluated},
    }


# ══════════════════════════════════════════════════════════
#  7. JOB APPLICATIONS GROUPED (Active Candidates)
# ══════════════════════════════════════════════════════════

@router.get("/applications-grouped", summary="List active applications grouped by job posting")
async def list_applications_grouped(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    """Returns active candidates grouped under their respective jobs, ordered by resume score."""
    q = (
        select(
            Application.id,
            Application.application_status,
            Application.resume_score,
            Application.match_score,
            Application.ranking_position,
            Application.hiring_confidence_score,
            Candidate.resume_quality_score.label("resume_quality_score"),
            Application.applied_at,
            Candidate.id.label("candidate_id"),
            Candidate.skills.label("candidate_skills"),
            User.name.label("candidate_name"),
            User.email.label("candidate_email"),
            Job.id.label("job_id"),
            Job.title.label("job_title"),
            Job.department.label("job_department"),
            Job.location.label("job_location"),
            Job.status.label("job_status"),
            Job.required_skills.label("job_required_skills")
        )
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.application_status == "Applied")
        .order_by(Job.id, Application.applied_at.desc())
    )
    
    try:
        result = await db.execute(q)
        rows = [dict(r) for r in result.mappings().all()]
    except Exception as e:
        print('Error fetching grouped applications:', e)
        raise HTTPException(status_code=500, detail='Internal server error while fetching applications')

    # Group by job
    grouped = OrderedDict()
    for r in rows:
        jid = r["job_id"]
        if jid not in grouped:
            grouped[jid] = {
                "job_id": jid,
                "job_title": r["job_title"],
                "job_department": r["job_department"],
                "job_location": r["job_location"],
                "job_status": r["job_status"],
                "job_required_skills": r["job_required_skills"],
                "candidates": []
            }
        grouped[jid]["candidates"].append({
            "application_id": r["id"],
            "candidate_id": r["candidate_id"],
            "candidate_name": r["candidate_name"],
            "candidate_email": r["candidate_email"],
            "application_status": r["application_status"],
            "resume_score": float(r["resume_score"]) if r["resume_score"] is not None else None,
            "match_score": float(r["match_score"]) if r["match_score"] is not None else None,
            "ranking_position": r["ranking_position"],
            "hiring_confidence_score": float(r["hiring_confidence_score"]) if r["hiring_confidence_score"] is not None else None,
            "candidate_skills": r["candidate_skills"],
            "resume_quality_score": float(r["resume_quality_score"]) if r["resume_quality_score"] is not None else None,
            "applied_at": str(r["applied_at"]) if r["applied_at"] else None,
        })
        
    return list(grouped.values())


# ══════════════════════════════════════════════════════════
#  8. CANDIDATE PIPELINE (stage-grouped)
# ══════════════════════════════════════════════════════════

@router.get("/pipeline", summary="Candidate pipeline grouped by stage")
async def candidate_pipeline(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    """Return all applications grouped by pipeline stage for kanban view."""
    q = (
        select(
            Application.id.label("application_id"),
            Application.application_status,
            Application.resume_score,
            Application.match_score,
            Application.interview_score,
            Candidate.id.label("candidate_id"),
            User.name.label("candidate_name"),
            User.email.label("candidate_email"),
            Job.id.label("job_id"),
            Job.title.label("job_title"),
        )
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .order_by(Application.applied_at.desc())
    )
    result = await db.execute(q)
    rows = [dict(r) for r in result.mappings().all()]

    stages = {
        "Shortlisted": [],
        "Interview Scheduled": [],
        "Interview In Progress": [],
        "Interview Completed": [],
        "Selected": [],
        "Rejected": [],
    }
    for r in rows:
        # Convert Decimal to float
        for k in ("resume_score", "match_score", "interview_score"):
            if r[k] is not None:
                r[k] = float(r[k])
        status = r["application_status"]
        if status in stages:
            stages[status].append(r)

    return stages


# ══════════════════════════════════════════════════════════
#  9. INTERVIEW FEEDBACK LISTING
# ══════════════════════════════════════════════════════════

@router.get("/interview-feedback", summary="Candidates with completed interview feedback")
async def interview_feedback_list(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    """Return candidates who have interview_results records for HR review."""
    q = (
        select(
            InterviewResult.id.label("result_id"),
            InterviewResult.application_id,
            InterviewResult.overall_score,
            InterviewResult.communication_score,
            InterviewResult.technical_score,
            InterviewResult.problem_solving_score,
            InterviewResult.confidence_score,
            InterviewResult.recommendation,
            InterviewResult.ai_feedback,
            InterviewResult.created_at.label("evaluated_at"),
            Application.application_status,
            User.name.label("candidate_name"),
            User.email.label("candidate_email"),
            Job.title.label("job_title"),
        )
        .join(Application, InterviewResult.application_id == Application.id)
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .order_by(InterviewResult.created_at.desc())
    )
    result = await db.execute(q)
    rows = []
    for r in result.mappings().all():
        d = dict(r)
        # Convert decimals
        for k in ("overall_score", "communication_score", "technical_score",
                   "problem_solving_score", "confidence_score"):
            if d[k] is not None:
                d[k] = float(d[k])
        if d["evaluated_at"]:
            d["evaluated_at"] = str(d["evaluated_at"])
        rows.append(d)
    return rows


# ══════════════════════════════════════════════════════════
#  10. FULL CANDIDATE PROFILE (aggregated AI data)
# ══════════════════════════════════════════════════════════

@router.get("/candidates/{application_id}/profile", summary="Full candidate profile with AI data")
async def candidate_full_profile(
    application_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    """Aggregate all AI analysis data for a candidate's application."""
    # Application + Candidate + User + Job
    q = (
        select(
            Application,
            Candidate.id.label("candidate_id"),
            Candidate.phone,
            Candidate.education,
            Candidate.experience,
            Candidate.resume_url,
            Candidate.skills,
            Candidate.certifications,
            Candidate.projects,
            Candidate.resume_summary,
            Candidate.resume_quality_score,
            Candidate.skill_strength_score,
            User.name.label("candidate_name"),
            User.email.label("candidate_email"),
            Job.id.label("job_id"),
            Job.title.label("job_title"),
            Job.required_skills.label("job_required_skills"),
            Job.department.label("job_department"),
            Job.experience_required.label("job_experience_required"),
        )
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    )
    result = await db.execute(q)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    app_obj = row[0]
    app_data = {c.name: getattr(app_obj, c.name) for c in Application.__table__.columns}
    # Convert Decimal fields
    for k in ("resume_score", "match_score", "interview_score", "hiring_confidence_score"):
        if app_data.get(k) is not None:
            app_data[k] = float(app_data[k])
    if app_data.get("applied_at"):
        app_data["applied_at"] = str(app_data["applied_at"])

    profile = {
        "application": app_data,
        "candidate": {
            "candidate_id": row.candidate_id,
            "name": row.candidate_name,
            "email": row.candidate_email,
            "phone": row.phone,
            "education": row.education,
            "experience": row.experience,
            "resume_url": row.resume_url,
            "skills": row.skills,
            "certifications": row.certifications,
            "projects": row.projects,
            "resume_summary": row.resume_summary,
            "resume_quality_score": float(row.resume_quality_score) if row.resume_quality_score else None,
            "skill_strength_score": float(row.skill_strength_score) if row.skill_strength_score else None,
        },
        "job": {
            "job_id": row.job_id,
            "title": row.job_title,
            "required_skills": row.job_required_skills,
            "department": row.job_department,
            "experience_required": row.job_experience_required,
        },
    }

    # Fetch interview result if exists
    ir_q = (
        select(InterviewResult)
        .where(InterviewResult.application_id == application_id)
        .order_by(InterviewResult.created_at.desc())
    )
    ir_result = await db.execute(ir_q)
    ir_obj = ir_result.scalar_one_or_none()
    if ir_obj:
        ir_data = {c.name: getattr(ir_obj, c.name) for c in InterviewResult.__table__.columns}
        for k in ("overall_score", "communication_score", "technical_score",
                   "problem_solving_score", "confidence_score"):
            if ir_data.get(k) is not None:
                ir_data[k] = float(ir_data[k])
        if ir_data.get("created_at"):
            ir_data["created_at"] = str(ir_data["created_at"])
        profile["interview_result"] = ir_data
    else:
        profile["interview_result"] = None

    return profile

@router.post("/candidates/{candidate_id}/parse-resume", summary="Parse resume file and extract data")
async def parse_candidate_resume(
    candidate_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    """Parse the candidate's resume file and extract education, experience, skills."""
    try:
        candidate = await cand_repo.get(db, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        resume_url = getattr(candidate, "resume_url", None)
        if not resume_url:
            raise HTTPException(status_code=400, detail="Candidate has no resume file")
        
        resume_path = resume_url.replace("/", "\\")
        parsed = parse_resume(resume_path)
        
        update_data = {
            "education": parsed.get("education"),
            "experience": parsed.get("experience"),
            "skills": parsed.get("skills"),
            "resume_summary": parsed.get("raw_text"),
        }
        
        await cand_repo.update(db, db_obj=candidate, obj_in=update_data)
        
        return {
            "success": True,
            "message": f"Resume parsed successfully",
            "data": parsed
        }
    except Exception as e:
        print(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/parse-all-resumes", summary="Parse all candidate resumes")
async def parse_all_resumes(
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    """Parse resumes for all candidates."""
    try:
        result = await db.execute(
            select(Candidate).where(Candidate.resume_url.isnot(None))
        )
        candidates = result.scalars().all()
        
        if not candidates:
            return {"success": True, "message": "No resumes to parse", "parsed_count": 0}
        
        parsed_count = 0
        for candidate in candidates:
            try:
                resume_path = candidate.resume_url.replace("/", "\\")
                parsed = parse_resume(resume_path)
                
                update_data = {
                    "education": parsed.get("education"),
                    "experience": parsed.get("experience"),
                    "skills": parsed.get("skills"),
                    "resume_summary": parsed.get("raw_text"),
                }
                
                await cand_repo.update(db, db_obj=candidate, obj_in=update_data)
                parsed_count += 1
                print(f"✅ Parsed resume for candidate {candidate.id}")
            except Exception as e:
                print(f"⚠️  Failed for candidate {candidate.id}: {e}")
                continue
        
        await db.commit()
        return {"success": True, "parsed_count": parsed_count, "total": len(candidates)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ══════════════════════════════════════════════════════════
#  11. POST-INTERVIEW HIRE / REJECT  (HR decision after AI interview)
# ══════════════════════════════════════════════════════════

@router.post("/applications/{application_id}/hire", summary="Hire candidate after AI interview")
async def hire_candidate(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr),
):
    q = (
        select(Application, User.name.label("name"), User.email.label("email"),
               User.id.label("user_id"), Candidate.id.label("cand_id"),
               Job.title.label("job_title"))
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    )
    result = await db.execute(q)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    app_obj, name, email, user_id, cand_id, job_title = row

    # Update statuses
    app_obj.application_status = "Hired"
    await db.execute(update(Candidate).where(Candidate.id == cand_id).values(current_status="Hired"))

    # In-app notification to candidate
    db.add(Notification(
        user_id=user_id,
        title="🎉 Congratulations — You're Hired!",
        message=f"We are delighted to offer you the position of {job_title}. Our onboarding team will reach out with next steps.",
    ))
    await db.commit()

    # Email candidate
    background_tasks.add_task(
        emailer.send_simple, email,
        f"Offer Letter — {job_title}",
        f"<p>Dear <b>{name}</b>,</p>"
        f"<p>Congratulations! After reviewing your AI interview, we are pleased to formally offer you the role of <b>{job_title}</b>.</p>"
        f"<p>Our team will be in touch shortly with your offer letter and onboarding details.</p>",
        True,
    )

    return {"detail": "Candidate hired", "application_id": application_id, "status": "Hired"}


@router.post("/applications/{application_id}/reject-post-interview", summary="Reject candidate after AI interview")
async def reject_candidate_post_interview(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr),
):
    q = (
        select(Application, User.name.label("name"), User.email.label("email"),
               User.id.label("user_id"), Candidate.id.label("cand_id"),
               Job.title.label("job_title"))
        .join(Candidate, Application.candidate_id == Candidate.id)
        .join(User, Candidate.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
        .where(Application.id == application_id)
    )
    result = await db.execute(q)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    app_obj, name, email, user_id, cand_id, job_title = row

    app_obj.application_status = "Rejected"
    await db.execute(update(Candidate).where(Candidate.id == cand_id).values(current_status="Rejected"))

    db.add(Notification(
        user_id=user_id,
        title="Application Update",
        message=f"Thank you for interviewing for {job_title}. After careful consideration, we will not be moving forward at this time.",
    ))
    await db.commit()

    background_tasks.add_task(
        emailer.send_simple, email,
        f"Application Update — {job_title}",
        f"<p>Dear <b>{name}</b>,</p>"
        f"<p>Thank you for your time and effort in the interview process for <b>{job_title}</b>.</p>"
        f"<p>After careful review, we will not be moving forward with your application at this time. We wish you the best in your search.</p>",
        True,
    )

    return {"detail": "Candidate rejected", "application_id": application_id, "status": "Rejected"}

"""
Add these endpoints to your hr.py file
These handle candidate selection, rejection, and hiring with email notifications
"""

# Add these imports at the top of hr.py:
from backend.services.sendgrid_email_service import SendGridEmailService, get_interview_invite_template, get_hired_template
from backend.models.models import User, Job, Candidate, Application
from sqlalchemy import select

# Initialize email service
email_service = SendGridEmailService()


# ═══════════════════════════════════════════════════════════════════════════
#  CANDIDATE SELECTION - SEND INTERVIEW INVITE EMAIL
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/applications/{application_id}/select", summary="Select candidate for interview")
async def select_candidate(
    application_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    """
    Select a candidate for interview and send email notification
    """
    try:
        application = await app_repo.get(db, application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Get candidate and job details
        candidate = await cand_repo.get(db, application.candidate_id)
        job = await job_repo.get(db, application.job_id)
        user = await db.get(User, candidate.user_id)
        
        if not candidate or not job or not user:
            raise HTTPException(status_code=404, detail="Candidate, job, or user not found")
        
        # Update application status to Shortlisted
        await app_repo.update(
            db,
            db_obj=application,
            obj_in={"application_status": "Shortlisted"}
        )
        
        # Send interview invite email
        email_html = get_interview_invite_template(
            candidate_name=user.name,
            job_title=job.title,
            company_name="Our Company"  # Change to your company name
        )
        
        email_sent = email_service.send_email(
            to_email=user.email,
            to_name=user.name,
            subject=f"Congratulations! You're Selected for {job.title} Interview",
            html_content=email_html
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Candidate selected and interview invite sent",
            "email_sent": email_sent,
            "application_id": application_id
        }
    
    except Exception as e:
        print(f"Error selecting candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
#  CANDIDATE REJECTION
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/applications/{application_id}/reject", summary="Reject candidate")
async def reject_candidate(
    application_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    """
    Reject a candidate application
    """
    try:
        application = await app_repo.get(db, application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Get candidate and job details
        candidate = await cand_repo.get(db, application.candidate_id)
        job = await job_repo.get(db, application.job_id)
        user = await db.get(User, candidate.user_id)
        
        if not candidate or not job or not user:
            raise HTTPException(status_code=404, detail="Candidate, job, or user not found")
        
        # Update application status to Rejected
        await app_repo.update(
            db,
            db_obj=application,
            obj_in={"application_status": "Rejected"}
        )
        
        # Optional: Send rejection email
        rejection_html = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Application Status Update</h2>
                <p>Hi {user.name},</p>
                <p>Thank you for your interest in the <strong>{job.title}</strong> position at Our Company.</p>
                <p>After careful review of your application and qualifications, we have decided to move forward with other candidates whose experience more closely aligns with our current needs.</p>
                <p>We appreciate your time and effort in applying. We encourage you to apply for future positions that match your profile.</p>
                <p>Best regards,<br>The HR Team</p>
            </div>
        </body>
        </html>
        """
        
        email_service.send_email(
            to_email=user.email,
            to_name=user.name,
            subject=f"Application Status: {job.title}",
            html_content=rejection_html
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Candidate rejected",
            "application_id": application_id
        }
    
    except Exception as e:
        print(f"Error rejecting candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
#  CANDIDATE HIRED - SEND JOB OFFER EMAIL
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/applications/{application_id}/hire", summary="Hire candidate and send offer")
async def hire_candidate(
    application_id: int,
    joining_date: str = "to be confirmed",  # Format: "YYYY-MM-DD" or description
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_hr)
):
    """
    Hire a candidate and send job offer email
    """
    try:
        application = await app_repo.get(db, application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Get candidate and job details
        candidate = await cand_repo.get(db, application.candidate_id)
        job = await job_repo.get(db, application.job_id)
        user = await db.get(User, candidate.user_id)
        
        if not candidate or not job or not user:
            raise HTTPException(status_code=404, detail="Candidate, job, or user not found")
        
        # Update application status to Selected/Hired
        await app_repo.update(
            db,
            db_obj=application,
            obj_in={"application_status": "Selected"}
        )
        
        # Send job offer email
        email_html = get_hired_template(
            candidate_name=user.name,
            job_title=job.title,
            company_name="Our Company",  # Change to your company name
            joining_date=joining_date
        )
        
        email_sent = email_service.send_email(
            to_email=user.email,
            to_name=user.name,
            subject=f"Job Offer: {job.title} Position",
            html_content=email_html
        )
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Candidate hired and offer email sent",
            "email_sent": email_sent,
            "application_id": application_id
        }
    
    except Exception as e:
        print(f"Error hiring candidate: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}") 

