from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from dependencies import get_request_context, RequestContext
import models

router = APIRouter(prefix="/api/crawls", tags=["crawls"])

@router.get("/{job_id}")
def get_crawl_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    # The frontend is sending the async_job.id. We need to find the related CrawlJob.
    # We can find the AsyncJob to get the product_id.
    async_job = db.query(models.AsyncJob).filter(models.AsyncJob.id == job_id).first()
    if not async_job:
        raise HTTPException(status_code=404, detail="Async Job not found")
        
    # Get the most recent CrawlJob for this product
    crawl_job = db.query(models.CrawlJob).filter(
        models.CrawlJob.product_id == async_job.product_id
    ).order_by(models.CrawlJob.created_at.desc()).first()
    
    if not crawl_job:
        raise HTTPException(status_code=404, detail="Crawl Job not found")
        
    return {
        "job_id": async_job.id,
        "status": crawl_job.status,
        "current_url": crawl_job.current_url,
        "pages_processed": crawl_job.pages_processed,
        "max_pages": crawl_job.max_pages,
        "error_message": async_job.error
    }

@router.get("/{job_id}/export")
def export_crawl_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    async_job = db.query(models.AsyncJob).filter(models.AsyncJob.id == job_id).first()
    if not async_job:
        raise HTTPException(status_code=404, detail="Async Job not found")
        
    crawl_job = db.query(models.CrawlJob).filter(
        models.CrawlJob.product_id == async_job.product_id
    ).order_by(models.CrawlJob.created_at.desc()).first()
    
    if not crawl_job:
        return {"screenshots": []}
        
    screenshots = db.query(models.PageScreenshot).filter(
        models.PageScreenshot.product_id == crawl_job.product_id
    ).all()
    
    screenshot_list = [
        {"storage_key": s.storage_key, "page_id": s.page_id} 
        for s in screenshots if s.storage_key
    ]
    
    return {"screenshots": screenshot_list}
