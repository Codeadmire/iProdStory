import time
import uuid
import httpx
from sqlalchemy.orm import Session
import models
from config import settings
from urllib.parse import urlencode

def generate_auth_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": settings.LINKEDIN_SCOPE,
    }
    return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

def exchange_code_for_token(code: str) -> dict:
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "client_secret": settings.LINKEDIN_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = httpx.post(url, data=data, headers=headers)
    response.raise_for_status()
    return response.json()

def get_linkedin_profile(access_token: str) -> dict:
    url = "https://api.linkedin.com/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = httpx.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def publish_campaign(campaign_post: models.CampaignPost, access_token: str, author_id: str) -> dict:
    # Build text content
    text = campaign_post.body
    if campaign_post.hashtags:
        text += f"\n\n{campaign_post.hashtags}"
        
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    payload = {
        "author": f"urn:li:person:{author_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    response = httpx.post(url, headers=headers, json=payload)
    if response.status_code != 201:
        return {"status": "error", "message": response.text}
        
    urn = response.headers.get("x-restli-id")
    return {
        "status": "success",
        "message": "Campaign published successfully",
        "linkedin_post_url": f"https://www.linkedin.com/feed/update/{urn}" if urn else None
    }

