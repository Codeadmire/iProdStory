"""
Celery task definitions.

IMPORTANT: Each task creates its OWN database session.
Never pass a SQLAlchemy Session across process/thread boundaries.
The API creates an AsyncJob record, enqueues the task with job_id,
then returns 202 immediately. The worker updates the job's status/progress.
"""
from datetime import datetime, timezone
import traceback
from celery import Task
from workers.celery_app import celery_app
from database import SessionLocal
import models


def _update_job(db, job_id: str, **kwargs):
    job = db.query(models.AsyncJob).filter(models.AsyncJob.id == job_id).first()
    if job:
        for k, v in kwargs.items():
            setattr(job, k, v)
        db.commit()


# ─── Base task with automatic job status management ───────────────────────────

class JobTask(Task):
    """Base task that wraps execution in try/finally to update job status."""
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job_id = kwargs.get("job_id") or (args[0] if args else None)
        if job_id:
            db = SessionLocal()
            try:
                _update_job(db, job_id,
                            status="failed",
                            error=str(exc),
                            completed_at=datetime.now(timezone.utc))
            finally:
                db.close()


# ─── Crawl ────────────────────────────────────────────────────────────────────

@celery_app.task(base=JobTask, bind=True, name="workers.tasks.crawl_product",
                 max_retries=2, default_retry_delay=30)
def crawl_product(self, job_id: str, product_id: str, crawl_job_id: str):
    """
    Crawls the product URL using Playwright, writes pages+screenshots to storage.
    Updates AsyncJob progress as it goes.
    """
    from services import crawler_service   # Lazy import to avoid circular deps
    db = SessionLocal()
    try:
        _update_job(db, job_id,
                    status="running",
                    started_at=datetime.now(timezone.utc),
                    celery_task_id=self.request.id)
        db.commit()
        crawler_service.run_crawler(crawl_job_id=crawl_job_id,
                                    product_id=product_id,
                                    db=db,
                                    progress_callback=lambda p: _update_job(db, job_id, progress=p))
        _update_job(db, job_id,
                    status="succeeded",
                    progress=100,
                    completed_at=datetime.now(timezone.utc))
        db.commit()
    except Exception as exc:
        _update_job(db, job_id,
                    status="failed",
                    error=traceback.format_exc(),
                    completed_at=datetime.now(timezone.utc))
        db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()


# ─── AI Analysis ──────────────────────────────────────────────────────────────

@celery_app.task(base=JobTask, bind=True, name="workers.tasks.analyze_product",
                 max_retries=2, default_retry_delay=60)
def analyze_product(self, job_id: str, product_id: str, model_name: str):
    from services import ai_service
    db = SessionLocal()
    try:
        _update_job(db, job_id, status="running",
                    started_at=datetime.now(timezone.utc),
                    celery_task_id=self.request.id)
        db.commit()
        ai_service.analyze_product_features(product_id=product_id, db=db, model_name=model_name)
        _update_job(db, job_id, status="succeeded", progress=100,
                    completed_at=datetime.now(timezone.utc))
        db.commit()
    except Exception as exc:
        _update_job(db, job_id, status="failed", error=traceback.format_exc(),
                    completed_at=datetime.now(timezone.utc))
        db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()


# ─── Media Generation ─────────────────────────────────────────────────────────

@celery_app.task(base=JobTask, bind=True, name="workers.tasks.generate_media",
                 max_retries=1, default_retry_delay=30)
def generate_media(self, job_id: str, product_id: str):
    from services import media_service
    db = SessionLocal()
    try:
        _update_job(db, job_id, status="running",
                    started_at=datetime.now(timezone.utc),
                    celery_task_id=self.request.id)
        db.commit()
        assets = media_service.generate_marketing_media(product_id=product_id, db=db)
        _update_job(db, job_id, status="succeeded", progress=100,
                    result=str(assets),
                    completed_at=datetime.now(timezone.utc))
        db.commit()
    except Exception as exc:
        _update_job(db, job_id, status="failed", error=traceback.format_exc(),
                    completed_at=datetime.now(timezone.utc))
        db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()


# ─── Campaign Generation ──────────────────────────────────────────────────────

@celery_app.task(base=JobTask, bind=True, name="workers.tasks.generate_campaign",
                 max_retries=2, default_retry_delay=60)
def generate_campaign(self, job_id: str, product_id: str, model_name: str):
    from services import campaign_service
    db = SessionLocal()
    try:
        _update_job(db, job_id, status="running",
                    started_at=datetime.now(timezone.utc),
                    celery_task_id=self.request.id)
        db.commit()
        campaign_service.generate_campaign(product_id=product_id, db=db, model_name=model_name)
        _update_job(db, job_id, status="succeeded", progress=100,
                    completed_at=datetime.now(timezone.utc))
        db.commit()
    except Exception as exc:
        _update_job(db, job_id, status="failed", error=traceback.format_exc(),
                    completed_at=datetime.now(timezone.utc))
        db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(base=JobTask, bind=True, name="workers.tasks.generate_posts",
                 max_retries=2, default_retry_delay=60)
def generate_posts(self, job_id: str, product_id: str, model_name: str, settings_dict: dict):
    from services import campaign_service
    db = SessionLocal()
    try:
        _update_job(db, job_id, status="running",
                    started_at=datetime.now(timezone.utc),
                    celery_task_id=self.request.id)
        db.commit()
        campaign_service.generate_linkedin_posts(product_id=product_id, db=db,
                                                  model_name=model_name,
                                                  settings=settings_dict)
        _update_job(db, job_id, status="succeeded", progress=100,
                    completed_at=datetime.now(timezone.utc))
        db.commit()
    except Exception as exc:
        _update_job(db, job_id, status="failed", error=traceback.format_exc(),
                    completed_at=datetime.now(timezone.utc))
        db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(base=JobTask, bind=True, name="workers.tasks.generate_product_page",
                 max_retries=2, default_retry_delay=60)
def generate_product_page(self, job_id: str, product_id: str, model_name: str):
    from services import campaign_service
    db = SessionLocal()
    try:
        _update_job(db, job_id, status="running",
                    started_at=datetime.now(timezone.utc),
                    celery_task_id=self.request.id)
        db.commit()
        campaign_service.generate_linkedin_product_page(product_id=product_id,
                                                         db=db, model_name=model_name)
        _update_job(db, job_id, status="succeeded", progress=100,
                    completed_at=datetime.now(timezone.utc))
        db.commit()
    except Exception as exc:
        _update_job(db, job_id, status="failed", error=traceback.format_exc(),
                    completed_at=datetime.now(timezone.utc))
        db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()
