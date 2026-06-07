from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_async_db
from backend.services.candidate_service import CandidateService
from backend.api.deps import get_current_active_candidate
from backend.schemas.schemas import UserCreate
from backend.schemas.schemas import UserResponse
from backend.schemas.schemas import NotificationResponse
from typing import List

router = APIRouter(prefix="/api/candidate", tags=["Candidate"])
service = CandidateService()


@router.post('/register', response_model=UserResponse)
async def register(req: UserCreate, db: AsyncSession = Depends(get_async_db)):
    # only allow role candidate
    try:
        user = await service.register(db, user_in=req.dict())
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/login')
async def login(body: dict, db: AsyncSession = Depends(get_async_db)):
    email = body.get('email')
    password = body.get('password')
    result = await service.login(db, email, password)
    if not result:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    return result


@router.get('/profile')
async def profile(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_candidate)):
    candidate = await service.get_profile(db, current_user)
    if not candidate:
        raise HTTPException(status_code=404, detail='Candidate profile not found')
    return candidate


@router.get('/jobs')
async def list_jobs(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_async_db)):
    return await service.list_jobs(db, skip=skip, limit=limit)


@router.post('/jobs/{job_id}/apply')
async def apply_job(job_id: int, db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_candidate)):
    # fetch candidate id
    from backend.repositories.candidate_repository import CandidateRepository
    cand_repo = CandidateRepository()
    candidate = await cand_repo.get_by_user_id(db, current_user.id)
    if not candidate:
        raise HTTPException(status_code=404, detail='Candidate profile not found')
    app = await service.apply_to_job(db, candidate.id, job_id)
    return app


@router.post('/upload_resume')
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_candidate)):
    # save file to uploads/ and update candidate.resume_url
    UPLOAD_DIR = 'uploads'
    import os
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, 'wb') as f:
        content = await file.read()
        f.write(content)

    from backend.repositories.candidate_repository import CandidateRepository
    cand_repo = CandidateRepository()
    candidate = await cand_repo.get_by_user_id(db, current_user.id)
    if not candidate:
        raise HTTPException(status_code=404, detail='Candidate not found')
    await cand_repo.update(db, db_obj=candidate, obj_in={'resume_url': path})
    return {'resume_url': path}


@router.get('/applications')
async def list_applications(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_candidate)):
    from backend.repositories.candidate_repository import CandidateRepository
    cand_repo = CandidateRepository()
    candidate = await cand_repo.get_by_user_id(db, current_user.id)
    if not candidate:
        raise HTTPException(status_code=404, detail='Candidate not found')
    return await service.list_applications(db, candidate.id)


@router.get('/notifications', response_model=List[NotificationResponse])
async def notifications(db: AsyncSession = Depends(get_async_db), current_user=Depends(get_current_active_candidate)):
    # reuse notification repo
    from backend.repositories.notification_repository import NotificationRepository
    nrepo = NotificationRepository()
    return await nrepo.list_for_user(db, current_user.id)
