"""
JWT authentication utilities.
- Password hashing with bcrypt (direct, avoids passlib Python 3.13 compat issues)
- Access token creation and verification
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt
from config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, workspace_id: Optional[str] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "workspace_id": workspace_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.InvalidTokenError on failure — callers must handle."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
