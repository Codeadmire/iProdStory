"""
Auth routes: register, login, /me
"""
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
import models
from auth import hash_password, verify_password, create_access_token
from dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _make_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "workspace"


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    workspace_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    workspace_id: str
    user_id: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = models.User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
    )
    db.add(user)
    db.flush()  # Get user.id before commit

    # Create a default workspace for the new user
    slug = _make_slug(req.workspace_name)
    # Ensure slug uniqueness
    existing = db.query(models.Workspace).filter(models.Workspace.slug == slug).first()
    if existing:
        slug = f"{slug}-{user.id[:6]}"

    workspace = models.Workspace(
        name=req.workspace_name,
        slug=slug,
        owner_id=user.id,
    )
    db.add(workspace)
    db.flush()

    member = models.WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role="owner",
    )
    db.add(member)
    db.commit()

    token = create_access_token(user_id=user.id, workspace_id=workspace.id)
    return TokenResponse(access_token=token, workspace_id=workspace.id, user_id=user.id)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    # Return first workspace the user owns (they can switch later)
    member = (db.query(models.WorkspaceMember)
              .filter(models.WorkspaceMember.user_id == user.id,
                      models.WorkspaceMember.role == "owner")
              .first())
    workspace_id = member.workspace_id if member else ""

    token = create_access_token(user_id=user.id, workspace_id=workspace_id)
    return TokenResponse(access_token=token, workspace_id=workspace_id, user_id=user.id)


@router.get("/me")
def me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
    }
