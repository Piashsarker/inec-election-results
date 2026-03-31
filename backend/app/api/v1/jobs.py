"""Jobs API endpoints.

Provides endpoints for managing scraping jobs.

Requirements: 6.1, 6.2, 6.3, 6.6
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models import ScrapingJob

router = APIRouter()


class CreateJobRequest(BaseModel):
    """Request to create a scraping job."""
    election_type: Optional[str] = None
    target_state: Optional[str] = None
    target_lga: Optional[str] = None
    target_ward: Optional[str] = None


class JobResponse(BaseModel):
    """Scraping job response schema."""
    id: UUID
    status: str
    election_type: Optional[str]
    target_state: Optional[str]
    target_lga: Optional[str]
    target_ward: Optional[str]
    total_polling_units: int
    processed_count: int
    success_count: int
    failed_count: int

    class Config:
        from_attributes = True


@router.post("/scrape", response_model=JobResponse)
async def start_scraping_job(
    request: CreateJobRequest,
    session: AsyncSession = Depends(get_async_session),
) -> JobResponse:
    """Start a new scraping job.
    
    Args:
        request: Job configuration with optional scope filters
        
    Returns:
        Created job with ID for tracking
    """
    job = ScrapingJob(
        status="queued",
        election_type=request.election_type,
        target_state=request.target_state,
        target_lga=request.target_lga,
        target_ward=request.target_ward,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    
    # In production, this would trigger a Celery task
    # celery_app.send_task('scrape_job', args=[str(job.id)])
    
    return JobResponse.model_validate(job)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> JobResponse:
    """Get status of a scraping job.
    
    Args:
        job_id: Job UUID
        
    Returns:
        Job status and progress
    """
    result = await session.execute(
        select(ScrapingJob).where(ScrapingJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse.model_validate(job)


@router.post("/{job_id}/pause", response_model=JobResponse)
async def pause_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> JobResponse:
    """Pause a running scraping job.
    
    Args:
        job_id: Job UUID
        
    Returns:
        Updated job status
    """
    result = await session.execute(
        select(ScrapingJob).where(ScrapingJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "running":
        raise HTTPException(status_code=400, detail="Job is not running")
    
    job.status = "paused"
    await session.commit()
    await session.refresh(job)
    
    return JobResponse.model_validate(job)


@router.post("/{job_id}/resume", response_model=JobResponse)
async def resume_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> JobResponse:
    """Resume a paused scraping job.
    
    Args:
        job_id: Job UUID
        
    Returns:
        Updated job status
    """
    result = await session.execute(
        select(ScrapingJob).where(ScrapingJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "paused":
        raise HTTPException(status_code=400, detail="Job is not paused")
    
    job.status = "running"
    await session.commit()
    await session.refresh(job)
    
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", response_model=JobResponse)
async def cancel_job(
    job_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> JobResponse:
    """Cancel a scraping job.
    
    Args:
        job_id: Job UUID
        
    Returns:
        Updated job status
    """
    result = await session.execute(
        select(ScrapingJob).where(ScrapingJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in ("completed", "cancelled", "failed"):
        raise HTTPException(status_code=400, detail=f"Job is already {job.status}")
    
    job.status = "cancelled"
    await session.commit()
    await session.refresh(job)
    
    return JobResponse.model_validate(job)
