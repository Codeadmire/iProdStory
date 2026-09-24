"""
JWT authentication utilities.
- Password hashing with bcrypt
- Access token creation and verification
- No refresh token rotation yet (Phase 2 feature)
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


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
