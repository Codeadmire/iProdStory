from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os

import models, schemas, database, crawler

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Product Marketing AI")

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount screenshots directory
import os
os.makedirs("screenshots", exist_ok=True)
os.makedirs("media_assets", exist_ok=True)
app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")
app.mount("/media_assets", StaticFiles(directory="media_assets"), name="media_assets")

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/products", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(database.get_db)):
    db_product = models.Product(base_url=product.url, name=product.url)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/api/products/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: str, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.post("/api/products/{product_id}/crawl")
def start_crawl(product_id: str, config: schemas.CrawlStartRequest, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db_job = models.CrawlJob(
        product_id=product_id, 
        status="RUNNING",
        max_pages=config.max_pages,
        max_depth=config.max_depth,
        timeout=config.timeout
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    background_tasks.add_task(crawler.run_crawler, db_job.id, db_product.base_url)
    return {"job_id": db_job.id, "status": "Started"}

import ai_service
@app.post("/api/products/{product_id}/analyze")
def start_ai_analysis(product_id: str, background_tasks: BackgroundTasks, config: schemas.AIModelConfig = None, db: Session = Depends(database.get_db)):
    if not config: config = schemas.AIModelConfig()
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    background_tasks.add_task(ai_service.analyze_product_features, product_id, db, config.model)
    return {"status": "Started AI Analysis", "model": config.model}

@app.get("/api/products/{product_id}/modules")
def get_product_modules(product_id: str, db: Session = Depends(database.get_db)):
    # Get modules with their features
    modules = db.query(models.Module).filter(models.Module.product_id == product_id).all()
    result = []
    for m in modules:
        m_features = db.query(models.Feature).filter(models.Feature.module_id == m.id).all()
        result.append({
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "features": [{"id": f.id, "name": f.name, "confidence": f.confidence} for f in m_features]
        })
    return result

@app.get("/api/crawls/{job_id}", response_model=schemas.CrawlJobResponse)
def get_crawl_job(job_id: str, db: Session = Depends(database.get_db)):
    db_job = db.query(models.CrawlJob).filter(models.CrawlJob.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    return db_job

@app.get("/api/products/{product_id}/pages", response_model=List[schemas.CrawledPageResponse])
def get_product_pages(product_id: str, db: Session = Depends(database.get_db)):
    pages = db.query(models.CrawledPage).filter(models.CrawledPage.product_id == product_id).all()
    return pages

@app.get("/api/products/{product_id}/features", response_model=List[schemas.FeatureResponse])
def get_product_features(product_id: str, db: Session = Depends(database.get_db)):
    features = db.query(models.Feature).filter(models.Feature.product_id == product_id).all()
    return features

@app.get("/api/crawls/{job_id}/export")
def export_crawl_data(job_id: str, db: Session = Depends(database.get_db)):
    job = db.query(models.CrawlJob).filter(models.CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Crawl job not found")
        
    product = db.query(models.Product).filter(models.Product.id == job.product_id).first()
    pages = db.query(models.CrawledPage).filter(models.CrawledPage.product_id == product.id).all()
    features = db.query(models.Feature).filter(models.Feature.product_id == product.id).all()
    screenshots = db.query(models.PageScreenshot).filter(models.PageScreenshot.product_id == product.id).all()
    
    return {
        "product": {"id": product.id, "base_url": product.base_url},
        "job": {"id": job.id, "status": job.status, "pages_processed": job.pages_processed},
        "pages": [{"id": p.id, "url": p.url, "title": p.title, "h1": p.h1, "status": p.status, "error_message": p.error_message} for p in pages],
        "features": [{"id": f.id, "name": f.name, "confidence": f.confidence} for f in features],
        "screenshots": [{"id": s.id, "page_id": s.page_id, "image_path": s.image_path} for s in screenshots]
    }

import media_service
import export_service
from fastapi.responses import StreamingResponse

@app.post("/api/products/{product_id}/media")
def generate_media(product_id: str, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    # In a real app we'd dispatch a background task, but for the demo we'll do it sync or mock
    assets = media_service.generate_marketing_media(product_id, db)
    return {"status": "success", "assets": assets}

@app.get("/api/products/{product_id}/export")
def export_campaign_zip(product_id: str, db: Session = Depends(database.get_db)):
    zip_buffer = export_service.create_export_zip(product_id, db)
    if not zip_buffer:
        raise HTTPException(status_code=404, detail="Product not found or failed to create export")
        
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={
            "Content-Disposition": f"attachment; filename=marketing_campaign_{product_id}.zip"
        }
    )

import linkedin_service

@app.get("/api/linkedin/auth/url")
def get_linkedin_auth_url():
    return {"url": linkedin_service.generate_auth_url()}

@app.post("/api/products/{product_id}/publish")
def publish_to_linkedin(product_id: str, db: Session = Depends(database.get_db)):
    result = linkedin_service.mock_publish_campaign(product_id, db)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

import campaign_service
@app.post("/api/products/{product_id}/campaign", response_model=schemas.CampaignResponse)
def generate_campaign(product_id: str, config: schemas.AIModelConfig = None, db: Session = Depends(database.get_db)):
    if not config: config = schemas.AIModelConfig()
    campaign = campaign_service.generate_campaign(product_id, db, config.model)
    if not campaign:
        raise HTTPException(status_code=404, detail="Product not found")
    return campaign

@app.get("/api/products/{product_id}/campaign", response_model=schemas.CampaignResponse)
def get_campaign(product_id: str, db: Session = Depends(database.get_db)):
    db_campaign = db.query(models.Campaign).filter(models.Campaign.product_id == product_id).first()
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign_service.get_campaign_dict(db_campaign, db)

@app.put("/api/campaigns/{campaign_id}", response_model=schemas.CampaignResponse)
def update_campaign(campaign_id: str, update: schemas.CampaignUpdate, db: Session = Depends(database.get_db)):
    db_campaign = db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    db_campaign.headline = update.headline
    db_campaign.about = update.about
    db.commit()
    
    db.query(models.CampaignPost).filter(models.CampaignPost.campaign_id == campaign_id).delete()
    for post in update.posts:
        db.add(models.CampaignPost(
            campaign_id=campaign_id,
            topic=post.topic,
            hook=post.hook,
            body=post.body,
            cta=post.cta,
            hashtags=post.hashtags,
            status=post.status
        ))
    db.commit()
    
    return campaign_service.get_campaign_dict(db_campaign, db)

@app.post("/api/products/{product_id}/product-page", response_model=schemas.ProductPageResponse)
def generate_product_page(product_id: str, config: schemas.AIModelConfig = None, db: Session = Depends(database.get_db)):
    if not config: config = schemas.AIModelConfig()
    page = campaign_service.generate_linkedin_product_page(product_id, db, config.model)
    if not page:
        raise HTTPException(status_code=404, detail="Product not found")
    return page

@app.get("/api/products/{product_id}/product-page", response_model=schemas.ProductPageResponse)
def get_product_page(product_id: str, db: Session = Depends(database.get_db)):
    page = db.query(models.LinkedInProductPage).filter(models.LinkedInProductPage.product_id == product_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Product Page not found")
    return page

@app.put("/api/products/{product_id}/product-page", response_model=schemas.ProductPageResponse)
def update_product_page(product_id: str, update: schemas.ProductPageUpdate, db: Session = Depends(database.get_db)):
    page = db.query(models.LinkedInProductPage).filter(models.LinkedInProductPage.product_id == product_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Product Page not found")
        
    page.name = update.name
    page.tagline = update.tagline
    page.description = update.description
    page.website = update.website
    page.target_audience = update.target_audience
    page.highlights = update.highlights
    page.status = update.status
    db.commit()
    db.refresh(page)
    return page

@app.post("/api/products/{product_id}/posts/generate", response_model=List[schemas.CampaignPostResponse])
def generate_posts(product_id: str, settings: schemas.PostGenerationSettings, db: Session = Depends(database.get_db)):
    posts = campaign_service.generate_linkedin_posts(product_id, db, settings.model, settings.dict())
    if posts is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return posts

@app.get("/api/products/{product_id}/posts", response_model=List[schemas.CampaignPostResponse])
def get_posts(product_id: str, db: Session = Depends(database.get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.product_id == product_id).first()
    if not campaign:
        return []
    posts = db.query(models.CampaignPost).filter(models.CampaignPost.campaign_id == campaign.id).all()
    return posts

@app.put("/api/products/{product_id}/posts", response_model=List[schemas.CampaignPostResponse])
def save_posts(product_id: str, updates: List[schemas.CampaignPostResponse], db: Session = Depends(database.get_db)):
    campaign = db.query(models.Campaign).filter(models.Campaign.product_id == product_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    db.query(models.CampaignPost).filter(models.CampaignPost.campaign_id == campaign.id).delete()
    db_posts = []
    for p in updates:
        db_post = models.CampaignPost(
            campaign_id=campaign.id,
            topic=p.topic,
            hook=p.hook,
            body=p.body,
            cta=p.cta,
            hashtags=p.hashtags,
            status=p.status
        )
        db.add(db_post)
        db_posts.append(db_post)
    db.commit()
    return db_posts
