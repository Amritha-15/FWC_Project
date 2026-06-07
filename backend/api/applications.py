from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, time
from backend.database.session import get_async_db, async_session_maker
from backend.api.deps import get_current_user
from backend.models.models import Application, Candidate, Notification, InterviewSchedule
from backend.services.sendgrid_email_service import SendGridEmailService
from backend.services.onboarding_service import OnboardingService
from backend.repositories.audit_repository import AuditRepository
import asyncio
from sqlalchemy import text

router = APIRouter(prefix="/api/applications", tags=["Applications"])
emailer = SendGridEmailService() 
audit_repo = AuditRepository()
onboard_service = OnboardingService()


@router.post("/{application_id}/shortlist")
async def shortlist_application(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    # fetch application
    res = await db.execute(Application.__table__.select().where(Application.__table__.c.id == application_id))
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    app = dict(row._mapping)
    candidate_id = app.get('candidate_id')

    # update statuses
    await db.execute(Application.__table__.update().where(Application.__table__.c.id == application_id).values(application_status='Shortlisted'))
    await db.execute(Candidate.__table__.update().where(Candidate.__table__.c.id == candidate_id).values(current_status='Shortlisted'))
    await db.commit()

    # create notification
    notif = Notification(user_id=app.get('candidate_id') and None, title='Application Shortlisted', message=f'Your application #{application_id} has been shortlisted.')
    # attempt to resolve user_id from candidate
    cand = await db.execute(Candidate.__table__.select().where(Candidate.__table__.c.id == candidate_id))
    crow = cand.first()
    user_id = None
    user_email = None
    if crow:
        cdict = dict(crow)
        user_id = cdict.get('user_id')
        notif.user_id = user_id

    db.add(notif)
    await db.commit()

    # audit log
    try:
        await audit_repo.create_log(db, admin_id=current_user.id, action=f"Shortlisted application {application_id}", target_user_id=user_id)
    except Exception:
        pass

    # send email in background
    if user_id:
        # fetch email
        r = await db.execute(
    text(
        "SELECT email FROM users WHERE id = :uid"
    ),
    {"uid": user_id}
)
        rr = r.first()
        if rr:
            user_email = rr[0]
            subject = 'You have been shortlisted'
            html = f"<p>Congratulations — your application (ID: {application_id}) has been shortlisted. We will contact you with next steps.</p>"
            background_tasks.add_task(emailer.send_simple, user_email, subject, html, True)

    return {"detail": "Application shortlisted", "application_id": application_id}


@router.post("/{application_id}/reject")
async def reject_application(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    res = await db.execute(Application.__table__.select().where(Application.__table__.c.id == application_id))
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    app = dict(row._mapping)
    candidate_id = app.get('candidate_id')

    await db.execute(Application.__table__.update().where(Application.__table__.c.id == application_id).values(application_status='Rejected'))
    await db.execute(Candidate.__table__.update().where(Candidate.__table__.c.id == candidate_id).values(current_status='Rejected'))
    await db.commit()

    # create notification
    cand = await db.execute(Candidate.__table__.select().where(Candidate.__table__.c.id == candidate_id))
    crow = cand.first()
    user_email = None
    user_id = None
    if crow:
        cdict = dict(crow)
        user_id = cdict.get('user_id')
        notif = Notification(user_id=user_id, title='Application Update', message=f'Your application #{application_id} has been rejected.')
        db.add(notif)
        await db.commit()

        r = await db.execute("select email from users where id = :uid", {'uid': user_id})
        rr = r.first()
        if rr:
            user_email = rr[0]
            subject = 'Application update'
            html = f"<p>We appreciate your interest. Unfortunately, your application (ID: {application_id}) was not selected.</p>"
            background_tasks.add_task(emailer.send_simple, user_email, subject, html, True)

    try:
        await audit_repo.create_log(db, admin_id=current_user.id, action=f"Rejected application {application_id}", target_user_id=user_id)
    except Exception:
        pass

    return {"detail": "Application rejected", "application_id": application_id}


@router.post("/{application_id}/schedule-interview")
async def schedule_interview(
    application_id: int,
    interview_date: date,
    interview_time: time,
    meeting_link: str | None = None,
    notes: str | None = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    res = await db.execute(Application.__table__.select().where(Application.__table__.c.id == application_id))
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    app = dict(row._mapping)
    candidate_id = app.get('candidate_id')
    job_id = app.get('job_id')

    # create schedule
    ins = InterviewSchedule.__table__.insert().values(candidate_id=candidate_id, job_id=job_id, application_id=application_id, interview_date=interview_date, interview_time=interview_time, meeting_link=meeting_link, notes=notes)
    await db.execute(ins)
    await db.execute(Application.__table__.update().where(Application.__table__.c.id == application_id).values(application_status='Interview Scheduled'))
    await db.execute(Candidate.__table__.update().where(Candidate.__table__.c.id == candidate_id).values(current_status='Interview Scheduled'))
    await db.commit()

    # notification + email
    cand = await db.execute(Candidate.__table__.select().where(Candidate.__table__.c.id == candidate_id))
    crow = cand.first()
    user_id = None
    if crow:
        cdict = dict(crow)
        user_id = cdict.get('user_id')
        notif = Notification(user_id=user_id, title='Interview Scheduled', message=f'Your interview is scheduled for {interview_date} at {interview_time}.')
        db.add(notif)
        await db.commit()

        r = await db.execute("select email from users where id = :uid", {'uid': user_id})
        rr = r.first()
        if rr and background_tasks:
            subject = 'Interview Scheduled'
            html = f"<p>Your interview for application {application_id} is scheduled on {interview_date} at {interview_time}. Meeting link: {meeting_link or 'TBD'}</p>"
            background_tasks.add_task(emailer.send_simple, rr[0], subject, html, True)

    try:
        await audit_repo.create_log(db, admin_id=current_user.id, action=f"Scheduled interview for application {application_id}", target_user_id=user_id)
    except Exception:
        pass

    return {"detail": "Interview scheduled", "application_id": application_id}


@router.post("/{application_id}/select")
async def select_application(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    res = await db.execute(Application.__table__.select().where(Application.__table__.c.id == application_id))
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    app = dict(row._mapping)
    candidate_id = app.get('candidate_id')

    # Guard: don't re-select an already selected application
    current_status = app.get('application_status', '')
    if current_status == 'Selected':
        raise HTTPException(status_code=400, detail="Candidate is already selected")

    print("Select endpoint called, application_id:", application_id, "candidate_id:", candidate_id)
    await db.execute(Application.__table__.update().where(Application.__table__.c.id == application_id).values(application_status='Selected'))
    await db.execute(Candidate.__table__.update().where(Candidate.__table__.c.id == candidate_id).values(current_status='Selected'))
    await db.commit()

    # create notification
    cand = await db.execute(Candidate.__table__.select().where(Candidate.__table__.c.id == candidate_id))
    crow = cand.first()
    user_id = None
    user_email = None
    if crow:
        cdict = dict(crow)
        user_id = cdict.get('user_id')
        notif = Notification(user_id=user_id, title='Application Selected', message=f'Congratulations! Your application #{application_id} has been selected.')
        db.add(notif)
        await db.commit()

        r = await db.execute("select email from users where id = :uid", {'uid': user_id})
        rr = r.first()
        if rr:
            user_email = rr[0]
            subject = 'Offer - Next Steps'
            html = f"<p>Congratulations — you have been selected for the role. Our onboarding team will reach out with next steps.</p>"
            background_tasks.add_task(emailer.send_simple, user_email, subject, html, True)

    # audit log
    try:
        await audit_repo.create_log(db, admin_id=current_user.id, action=f"Selected application {application_id}", target_user_id=user_id)
    except Exception:
        pass

    # trigger onboarding in background using its own async session
    def _onboard_worker(cand_id):
        async def _run():
            async with async_session_maker() as session:
                try:
                    await onboard_service.onboard_candidate(session, cand_id)
                except Exception:
                    pass
        asyncio.run(_run())

    background_tasks.add_task(_onboard_worker, candidate_id)

    return {"detail": "Application selected and onboarding triggered", "application_id": application_id}
@router.get("/")
async def list_applications(db: AsyncSession = Depends(get_async_db), current_user = Depends(get_current_user)):
    res = await db.execute(Application.__table__.select())
    rows = res.fetchall()
    apps = [dict(row._mapping) for row in rows]
    return {"applications": apps}

# ══════════════════════════════════════════════════════════════════
#  CANDIDATE ENDPOINTS
# ══════════════════════════════════════════════════════════════════


@router.get("/candidate/applications")
async def candidate_list_applications(
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    try:
        from sqlalchemy import select
        from backend.models.models import Job
        
        # Get candidate record for current user
        cand_res = await db.execute(
            select(Candidate).where(Candidate.user_id == current_user.id)
        )
        candidate = cand_res.scalar_one_or_none()
        if not candidate:
            return []
        
        # Get all applications for this candidate with job details
        apps_res = await db.execute(
            select(
                Application.id,
                Application.job_id,
                Application.application_status,
                Application.applied_at,
                Application.resume_score,
                Application.match_score,
                Application.ranking_position,
                Application.interview_score,
                Job.title.label("job_title"),
            )
            .join(Job, Application.job_id == Job.id)
            .where(Application.candidate_id == candidate.id)
            .order_by(Application.applied_at.desc())
        )
        
        apps = []
        for row in apps_res.mappings().all():
            app_dict = dict(row)
            for key in ("resume_score", "match_score", "ranking_position", "interview_score"):
                if app_dict.get(key) is not None:
                    app_dict[key] = float(app_dict[key])
            apps.append(app_dict)
        
        return apps
    except Exception as e:
        print(f"Error in candidate_list_applications: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))