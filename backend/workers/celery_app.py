"""
Celery application factory.

The API process and the worker process both import this module.
The API enqueues tasks; the worker executes them.

Start the worker:
    celery -A workers.celery_app worker --loglevel=info --concurrency=2
"""
from celery import Celery
from config import settings

celery_app = Celery(
    "prodmarketing",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "workers.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,           # Only ack after task completes (safe retry)
    worker_prefetch_multiplier=1,  # Fair dispatch across workers
    task_routes={
        "workers.tasks.crawl_product": {"queue": "crawl"},
        "workers.tasks.analyze_product": {"queue": "ai"},
        "workers.tasks.generate_media": {"queue": "ai"},
        "workers.tasks.generate_campaign": {"queue": "ai"},
        "workers.tasks.generate_posts": {"queue": "ai"},
        "workers.tasks.generate_product_page": {"queue": "ai"},
    },
    task_default_queue="default",
)
