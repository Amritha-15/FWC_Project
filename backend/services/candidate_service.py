from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.user_repository import UserRepository
from backend.repositories.job_repository import JobRepository
from backend.repositories.application_repository import ApplicationRepository
from backend.repositories.notification_repository import NotificationRepository
from backend.core.security import get_password_hash, verify_password, create_access_token
from backend.models.models import User, Candidate
from backend.core.config import settings


class CandidateService:
    def __init__(self):
        self.candidate_repo = CandidateRepository()
        self.user_repo = UserRepository()
        self.job_repo = JobRepository()
        self.app_repo = ApplicationRepository()
        self.notification_repo = NotificationRepository()

    async def register(self, db: AsyncSession, user_in: Dict[str, Any]) -> User:
        # create user then candidate
        user_payload = {
            'name': user_in['name'],
            'email': user_in['email'],
            'password_hash': get_password_hash(user_in['password']),
            'role': 'candidate'
        }
        user = await self.user_repo.create(db, obj_in=user_payload)
        cand_payload = {
            'user_id': user.id,
            'phone': user_in.get('phone'),
            'education': user_in.get('education'),
            'skills': user_in.get('skills')
        }
        await self.candidate_repo.create(db, obj_in=cand_payload)
        return user

    async def login(self, db: AsyncSession, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = await self.user_repo.get_by_email(db, email)
        if not user:
            return None
        if user.role != 'candidate':
            return None
        if not verify_password(password, user.password_hash):
            return None
        token = create_access_token(subject={'id': user.id, 'email': user.email}, role=user.role)
        return {'access_token': token, 'token_type': 'bearer', 'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}}

    async def get_profile(self, db: AsyncSession, user: User) -> Optional[Candidate]:
        return await self.candidate_repo.get_by_user_id(db, user.id)

    async def list_jobs(self, db: AsyncSession, skip: int = 0, limit: int = 50):
        return await self.job_repo.list_open(db, skip=skip, limit=limit)

    async def apply_to_job(self, db: AsyncSession, candidate_id: int, job_id: int) -> Any:
        app = await self.app_repo.create(db, obj_in={'candidate_id': candidate_id, 'job_id': job_id})
        # create notification -- simplified
        await self.notification_repo.list_for_user(db, candidate_id)
        return app

    async def list_applications(self, db: AsyncSession, candidate_id: int, skip: int = 0, limit: int = 50):
        return await self.app_repo.list_for_candidate(db, candidate_id, skip=skip, limit=limit)
