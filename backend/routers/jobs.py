"""
Async job polling endpoint.
POST /api/{resource}/action  → 202 + job_id
GET  /api/jobs/{job_id}      → job status + progress
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from dependencies import get_request_context, RequestContext
import models

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    progress: int
    error: Optional[str]
    result: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    job = db.query(models.AsyncJob).filter(
        models.AsyncJob.id == job_id,
        models.AsyncJob.workspace_id == ctx.workspace.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress or 0,
        error=job.error,
        result=job.result,
        created_at=str(job.created_at),
        started_at=str(job.started_at) if job.started_at else None,
        completed_at=str(job.completed_at) if job.completed_at else None,
    )
