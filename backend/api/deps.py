from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.session import get_async_db
from backend.core.security import decode_token
from backend.repositories.user_repository import UserRepository
from backend.models.models import User

bearer_scheme = HTTPBearer()
user_repo = UserRepository()

async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract token from Bearer auth credentials
    token = credentials.credentials if credentials else None
    if not token:
        raise credentials_exception

    # Decode JWT
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
        
    email: str = payload.get("email")
    user_id: int = payload.get("id")
    if email is None or user_id is None:
        raise credentials_exception

    # Get user from database
    user = await user_repo.get(db, user_id)
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user profile"
        )
        
    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Role-Based Access Control dependency. Checks if role is 'admin'.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrator privileges required."
        )
    return current_user


def get_current_active_manager(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Role-Based Access Control dependency. Checks if role is 'manager'.
    """
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Manager privileges required."
        )
    return current_user


def get_current_active_employee(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Role-Based Access Control dependency. Checks if role is 'employee'.
    """
    if current_user.role != "employee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Employee privileges required."
        )
    return current_user


def get_current_active_candidate(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Role-Based Access Control dependency. Checks if role is 'candidate'.
    """
    if current_user.role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Candidate privileges required."
        )
    return current_user


def get_current_active_hr(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Role-Based Access Control dependency. Allows 'hr' and 'admin' roles.
    """
    if current_user.role not in ("hr", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. HR or Admin privileges required."
        )
    return current_user
