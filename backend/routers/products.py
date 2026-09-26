"""
Product + Crawl + AI Analysis routes.
All operations are scoped to the authenticated workspace.
Long-running tasks return 202 + a job_id to poll.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from dependencies import get_request_context, RequestContext
from utils.ssrf import validate_crawl_url
import models
from workers.tasks import (
    crawl_product as crawl_task,
    analyze_product as analyze_task,
    generate_media as media_task,
    generate_campaign as campaign_task,
    generate_posts as posts_task,
    generate_product_page as page_task,
)
from config import settings

router = APIRouter(prefix="/api/products", tags=["products"])


# ── Helper ────────────────────────────────────────────────────────────────────

def _create_job(db: Session, workspace_id: str, product_id: str, job_type: str) -> models.AsyncJob:
    job = models.AsyncJob(
        workspace_id=workspace_id,
        product_id=product_id,
        job_type=job_type,
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _require_product(product_id: str, workspace_id: str, db: Session) -> models.Product:
    p = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.workspace_id == workspace_id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    url: str
    name: Optional[str] = None

class CrawlConfig(BaseModel):
    max_pages: int = 50
    max_depth: int = 3
    timeout: int = 30_000

class AIConfig(BaseModel):
    model: str = "gemini-1.5-flash-002"

class PostGenerationSettings(BaseModel):
    num_posts: int = 3
    tone: str = "Professional B2B"
    audience: str = "Business Owners"
    content_types: List[str] = ["Product launch"]
    model: str = "gemini-1.5-flash-002"

class JobAccepted(BaseModel):
    job_id: str
    status: str = "PENDING"
    message: str


# ── Product CRUD ──────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_product(
    body: ProductCreate,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    clean_url = validate_crawl_url(body.url)
    product = models.Product(
        workspace_id=ctx.workspace.id,
        name=body.name or clean_url,
        base_url=clean_url,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": product.id, "name": product.name, "base_url": product.base_url,
            "status": product.status, "created_at": str(product.created_at)}


@router.get("")
def list_products(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    products = db.query(models.Product).filter(
        models.Product.workspace_id == ctx.workspace.id,
        models.Product.status != "archived",
    ).all()
    return [{"id": p.id, "name": p.name, "base_url": p.base_url, "created_at": str(p.created_at)}
            for p in products]


@router.get("/{product_id}")
def get_product(
    product_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    return _require_product(product_id, ctx.workspace.id, db)


# ── Crawl ─────────────────────────────────────────────────────────────────────

@router.post("/{product_id}/crawl", response_model=JobAccepted, status_code=202)
def start_crawl(
    product_id: str,
    config: CrawlConfig = CrawlConfig(),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    product = _require_product(product_id, ctx.workspace.id, db)

    crawl_job = models.CrawlJob(
        product_id=product_id,
        status="PENDING",
        max_pages=config.max_pages,
        max_depth=config.max_depth,
        timeout=config.timeout,
    )
    db.add(crawl_job)
    db.flush()

    async_job = _create_job(db, ctx.workspace.id, product_id, "crawl")

    # Enqueue — worker will create its own DB session
    crawl_task.delay(
        job_id=async_job.id,
        product_id=product_id,
        crawl_job_id=crawl_job.id,
    )

    return JobAccepted(job_id=async_job.id,
                       message=f"Crawl started for {product.base_url}")


# ── AI Analysis ───────────────────────────────────────────────────────────────

@router.post("/{product_id}/analyze", response_model=JobAccepted, status_code=202)
def start_analysis(
    product_id: str,
    config: AIConfig = AIConfig(),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    async_job = _create_job(db, ctx.workspace.id, product_id, "ai_analyze")
    
    actual_model = "gemini-1.5-flash-002"
        
    analyze_task.delay(job_id=async_job.id, product_id=product_id, model_name=actual_model)
    return JobAccepted(job_id=async_job.id, message="AI analysis queued")


# ── Intelligence Read Endpoints ───────────────────────────────────────────────

@router.get("/{product_id}/modules")
def get_modules(
    product_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    modules = db.query(models.Module).filter(
        models.Module.product_id == product_id
    ).order_by(models.Module.display_order).all()
    result = []
    for m in modules:
        feats = db.query(models.Feature).filter(models.Feature.module_id == m.id).all()
        result.append({
            "id": m.id, "name": m.name, "description": m.description,
            "features": [{"id": f.id, "name": f.name, "confidence": f.confidence} for f in feats],
        })
    return result


@router.get("/{product_id}/features")
def get_features(
    product_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    features = db.query(models.Feature).filter(
        models.Feature.product_id == product_id
    ).all()
    return [{"id": f.id, "name": f.name, "confidence": f.confidence} for f in features]


@router.get("/{product_id}/pages")
def get_pages(
    product_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    pages = db.query(models.CrawledPage).filter(
        models.CrawledPage.product_id == product_id
    ).all()
    return [{"id": p.id, "url": p.url, "title": p.title,
             "http_status": p.http_status, "depth": p.depth} for p in pages]


# ── Media ─────────────────────────────────────────────────────────────────────

@router.post("/{product_id}/media", response_model=JobAccepted, status_code=202)
def generate_media(
    product_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    async_job = _create_job(db, ctx.workspace.id, product_id, "media_generate")
    media_task.delay(job_id=async_job.id, product_id=product_id)
    return JobAccepted(job_id=async_job.id, message="Media generation queued")


# ── Campaign ──────────────────────────────────────────────────────────────────

@router.post("/{product_id}/campaign", response_model=JobAccepted, status_code=202)
def generate_campaign(
    product_id: str,
    config: AIConfig = AIConfig(),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    async_job = _create_job(db, ctx.workspace.id, product_id, "campaign_generate")
    
    actual_model = "gemini-1.5-flash-002"
        
    campaign_task.delay(job_id=async_job.id, product_id=product_id, model_name=actual_model)
    return JobAccepted(job_id=async_job.id, message="Campaign generation queued")


@router.get("/{product_id}/campaign")
def get_campaign(
    product_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    campaign = db.query(models.Campaign).filter(
        models.Campaign.product_id == product_id
    ).order_by(models.Campaign.created_at.desc()).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="No campaign yet")
    posts = db.query(models.CampaignPost).filter(
        models.CampaignPost.campaign_id == campaign.id
    ).all()
    return {
        "id": campaign.id,
        "headline": campaign.headline,
        "about": campaign.about,
        "status": campaign.status,
        "posts": [{"id": p.id, "topic": p.topic, "hook": p.hook,
                   "body": p.body, "cta": p.cta, "hashtags": p.hashtags,
                   "status": p.status} for p in posts],
    }


# ── LinkedIn Posts ────────────────────────────────────────────────────────────

@router.post("/{product_id}/posts/generate", response_model=JobAccepted, status_code=202)
def generate_posts(
    product_id: str,
    body: PostGenerationSettings,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    async_job = _create_job(db, ctx.workspace.id, product_id, "posts_generate")
    
    actual_model = "gemini-1.5-flash-002"
        
    posts_task.delay(job_id=async_job.id, product_id=product_id,
                     model_name=actual_model, settings_dict=body.dict())
    return JobAccepted(job_id=async_job.id, message="Post generation queued")


@router.get("/{product_id}/posts")
def get_posts(
    product_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    campaign = db.query(models.Campaign).filter(
        models.Campaign.product_id == product_id
    ).order_by(models.Campaign.created_at.desc()).first()
    if not campaign:
        return []
    posts = db.query(models.CampaignPost).filter(
        models.CampaignPost.campaign_id == campaign.id
    ).all()
    return [{"id": p.id, "topic": p.topic, "hook": p.hook,
             "body": p.body, "cta": p.cta, "hashtags": p.hashtags,
             "status": p.status} for p in posts]


# ── LinkedIn Product Page ─────────────────────────────────────────────────────

@router.post("/{product_id}/product-page", response_model=JobAccepted, status_code=202)
def generate_product_page(
    product_id: str,
    config: AIConfig = AIConfig(),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    async_job = _create_job(db, ctx.workspace.id, product_id, "product_page_generate")
    
    actual_model = "gemini-1.5-flash-002"
        
    page_task.delay(job_id=async_job.id, product_id=product_id, model_name=actual_model)
    return JobAccepted(job_id=async_job.id, message="Product page generation queued")


@router.get("/{product_id}/product-page")
def get_product_page(
    product_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    page = db.query(models.LinkedInProductPage).filter(
        models.LinkedInProductPage.product_id == product_id
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Product page not generated yet")
    return {k: v for k, v in page.__dict__.items() if not k.startswith("_")}


@router.put("/{product_id}/product-page")
def update_product_page(
    product_id: str,
    update: dict,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    _require_product(product_id, ctx.workspace.id, db)
    page = db.query(models.LinkedInProductPage).filter(
        models.LinkedInProductPage.product_id == product_id
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Product page not found")
    for field in ("name", "tagline", "description", "website", "target_audience",
                  "highlights", "status"):
        if field in update:
            setattr(page, field, update[field])
    db.commit()
    db.refresh(page)
    return {k: v for k, v in page.__dict__.items() if not k.startswith("_")}
