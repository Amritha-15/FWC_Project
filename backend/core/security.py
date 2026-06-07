import os
import bcrypt
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from backend.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a standard bcrypt hash.
    Compatible with both Node.js (bcryptjs) and Python (bcrypt) formats.
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Generates a bcrypt hash for a plain text password using 10 salt rounds.
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(10)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(subject: Union[str, Any], role: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload matches Node.js structure: id, email, role
    to_encode = {
        "exp": expire,
        "id": int(subject["id"]),
        "email": str(subject["email"]),
        "role": str(role)
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return decoded
    except Exception:
        return None
