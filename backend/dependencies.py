"""
FastAPI dependency injectors.

Usage in route:
    @router.get("/products")
    def list_products(
        ctx: RequestContext = Depends(get_request_context),
        db: Session = Depends(get_db),
    ):
        ...
"""
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
import jwt

from database import get_db
import models
from auth import decode_access_token


class RequestContext:
    """Carries authenticated user + active workspace for a request."""
    def __init__(self, user: models.User, workspace: models.Workspace):
        self.user = user
        self.workspace = workspace


def _get_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization.split(" ", 1)[1]


def get_current_user(
    token: str = Depends(_get_token),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_error
    except jwt.InvalidTokenError:
        raise credentials_error

    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.is_active == True,
    ).first()
    if not user:
        raise credentials_error
    return user


def get_request_context(
    workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RequestContext:
    """
    Resolve the active workspace from the X-Workspace-Id header.
    Enforces that the requesting user is a member of that workspace.
    """
    if not workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Workspace-Id header is required",
        )

    member = (
        db.query(models.WorkspaceMember)
        .filter(
            models.WorkspaceMember.workspace_id == workspace_id,
            models.WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace",
        )

    workspace = db.query(models.Workspace).filter(
        models.Workspace.id == workspace_id
    ).first()
    return RequestContext(user=current_user, workspace=workspace)


def require_workspace_role(*roles: str):
    """Return a dependency that enforces the caller has one of the given roles."""
    def _check(
        workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> models.WorkspaceMember:
        member = (
            db.query(models.WorkspaceMember)
            .filter(
                models.WorkspaceMember.workspace_id == workspace_id,
                models.WorkspaceMember.user_id == current_user.id,
                models.WorkspaceMember.role.in_(roles),
            )
            .first()
        )
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {list(roles)}",
            )
        return member
    return _check
