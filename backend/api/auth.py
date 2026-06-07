from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_async_db
from backend.repositories.user_repository import UserRepository
from backend.schemas.schemas import LoginRequest, Token
from backend.core.security import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
user_repo = UserRepository()

@router.post("/login", response_model=Token)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_async_db)):
    """
    Exposes Admin authentication. Validates credentials, role checks, and issues JWT tokens.
    """
    user = await user_repo.get_by_email(db, req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Password check
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Verify admin, hr, employee, or manager role is permitted access
    if user.role not in ["admin", "hr", "employee", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Insufficient privileges."
        )

    # Issue token
    subject = {"id": user.id, "email": user.email}
    access_token = create_access_token(subject=subject, role=user.role)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }
