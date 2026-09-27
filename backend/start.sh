#!/bin/bash
# Automatically run database migrations on startup
echo "Running database migrations..."
alembic upgrade head

# Start Celery worker in the background
celery -A workers.celery_app worker -Q crawl,ai,default --concurrency=1 --loglevel=info &
# Start Uvicorn in the foreground
uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
