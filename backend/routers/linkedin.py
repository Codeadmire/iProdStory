"""
LinkedIn OAuth2 + Publishing router.

Flow:
  1. GET  /api/linkedin/connect         → returns authorization URL
  2. GET  /api/linkedin/callback?code=  → exchanges code for tokens, saves SocialAccount
  3. POST /api/products/{id}/publish    → queues a publish job to LinkedIn

References:
  https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow
  https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugcposts
"""
import secrets
import httpx
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from dependencies import get_request_context, RequestContext
from config import settings
import models

router = APIRouter(prefix="/api/linkedin", tags=["linkedin"])

# ── Constants ─────────────────────────────────────────────────────────────────
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_PROFILE_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_UGC_POST_URL = "https://api.linkedin.com/v2/ugcPosts"


# ── In-memory state store (use Redis in production) ───────────────────────────
# Maps state → workspace_id for CSRF validation
_oauth_states: dict[str, str] = {}


# ── Step 1: Generate authorization URL ───────────────────────────────────────

@router.get("/connect")
def connect_linkedin(
    ctx: RequestContext = Depends(get_request_context),
):
    """Returns the LinkedIn OAuth2 authorization URL for this workspace."""
    if not settings.LINKEDIN_CLIENT_ID:
        raise HTTPException(status_code=501,
                            detail="LinkedIn OAuth not configured. Set LINKEDIN_CLIENT_ID.")

    state = secrets.token_urlsafe(24)
    _oauth_states[state] = ctx.workspace.id   # Bind state to workspace

    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": settings.LINKEDIN_SCOPE,
    }
    from urllib.parse import urlencode
    auth_url = f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"
    return {"authorization_url": auth_url, "state": state}


# ── Step 2: OAuth callback — exchange code for tokens ────────────────────────

@router.get("/callback")
def linkedin_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    LinkedIn redirects here after the user grants permission.
    Exchanges the code for an access token and saves the SocialAccount.
    """
    # CSRF check
    workspace_id = _oauth_states.pop(state, None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="LinkedIn OAuth not configured")

    # Exchange code for tokens
    try:
        resp = httpx.post(LINKEDIN_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        }, timeout=15)
        resp.raise_for_status()
        token_data = resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502,
                            detail=f"LinkedIn token exchange failed: {e}")

    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 3600)
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        raise HTTPException(status_code=502, detail="No access_token in LinkedIn response")

    # Fetch the user's LinkedIn profile
    try:
        profile_resp = httpx.get(LINKEDIN_PROFILE_URL,
                                 headers={"Authorization": f"Bearer {access_token}"},
                                 timeout=10)
        profile_resp.raise_for_status()
        profile = profile_resp.json()
    except httpx.HTTPError:
        profile = {}

    account_id = profile.get("sub", "unknown")
    account_name = profile.get("name") or profile.get("email", "LinkedIn Account")

    # Upsert SocialAccount
    existing = db.query(models.SocialAccount).filter(
        models.SocialAccount.workspace_id == workspace_id,
        models.SocialAccount.platform == "linkedin",
        models.SocialAccount.account_id == account_id,
    ).first()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    if existing:
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.token_expires_at = expires_at
        existing.account_name = account_name
        existing.is_active = True
    else:
        account = models.SocialAccount(
            workspace_id=workspace_id,
            platform="linkedin",
            account_id=account_id,
            account_name=account_name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=expires_at,
            scopes=settings.LINKEDIN_SCOPE,
        )
        db.add(account)

    db.commit()

    return {
        "status": "connected",
        "account_name": account_name,
        "platform": "linkedin",
        "message": "LinkedIn account connected successfully. You can close this window.",
    }


# ── Step 3: List connected social accounts ────────────────────────────────────

@router.get("/accounts")
def list_social_accounts(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    accounts = db.query(models.SocialAccount).filter(
        models.SocialAccount.workspace_id == ctx.workspace.id,
        models.SocialAccount.is_active == True,
    ).all()
    return [
        {
            "id": a.id,
            "platform": a.platform,
            "account_name": a.account_name,
            "scopes": a.scopes,
            "connected_at": str(a.connected_at),
            "token_expires_at": str(a.token_expires_at) if a.token_expires_at else None,
        }
        for a in accounts
    ]


@router.delete("/accounts/{account_id}")
def disconnect_social_account(
    account_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    account = db.query(models.SocialAccount).filter(
        models.SocialAccount.id == account_id,
        models.SocialAccount.workspace_id == ctx.workspace.id,
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account.is_active = False
    db.commit()
    return {"status": "disconnected"}


# ── Step 4: Publish a campaign post to LinkedIn ───────────────────────────────

class PublishRequest(BaseModel):
    campaign_post_id: str
    social_account_id: str


@router.post("/products/{product_id}/publish")
def publish_to_linkedin(
    product_id: str,
    body: PublishRequest,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    """
    Publishes a single CampaignPost to LinkedIn via the UGC Posts API.
    Creates a SocialPost record tracking the result.
    """
    # Verify product belongs to workspace
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.workspace_id == ctx.workspace.id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Verify social account belongs to workspace
    account = db.query(models.SocialAccount).filter(
        models.SocialAccount.id == body.social_account_id,
        models.SocialAccount.workspace_id == ctx.workspace.id,
        models.SocialAccount.is_active == True,
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Social account not found or disconnected")

    # Verify post exists
    post = db.query(models.CampaignPost).filter(
        models.CampaignPost.id == body.campaign_post_id,
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Campaign post not found")

    # Build post content
    content_parts = []
    if post.hook:
        content_parts.append(post.hook)
    if post.body:
        content_parts.append(post.body)
    if post.cta:
        content_parts.append(post.cta)
    if post.hashtags:
        content_parts.append(post.hashtags)
    full_content = "\n\n".join(content_parts)

    # Create SocialPost record
    social_post = models.SocialPost(
        campaign_id=post.campaign_id,
        campaign_post_id=post.id,
        social_account_id=account.id,
        platform="linkedin",
        content=full_content,
        status="publishing",
    )
    db.add(social_post)
    db.commit()
    db.refresh(social_post)

    # Call LinkedIn UGC Posts API
    ugc_payload = {
        "author": f"urn:li:person:{account.account_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": full_content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    try:
        linkedin_resp = httpx.post(
            LINKEDIN_UGC_POST_URL,
            json=ugc_payload,
            headers={
                "Authorization": f"Bearer {account.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            timeout=20,
        )
        linkedin_resp.raise_for_status()
        platform_post_id = linkedin_resp.headers.get("x-restli-id", "")

        social_post.status = "published"
        social_post.published_at = datetime.now(timezone.utc)
        social_post.platform_post_id = platform_post_id
        db.commit()

        return {
            "status": "published",
            "platform_post_id": platform_post_id,
            "linkedin_url": f"https://www.linkedin.com/feed/update/{platform_post_id}",
        }

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text[:500]
        social_post.status = "failed"
        social_post.error_message = error_detail
        db.commit()

        if e.response.status_code == 401:
            # Token expired — mark account inactive so user reconnects
            account.is_active = False
            db.commit()
            raise HTTPException(status_code=401,
                                detail="LinkedIn token expired. Please reconnect your account.")

        raise HTTPException(status_code=502,
                            detail=f"LinkedIn API error: {error_detail}")

    except httpx.RequestError as e:
        social_post.status = "failed"
        social_post.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=502, detail=f"Network error: {e}")
