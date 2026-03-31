"""Background tasks for INEC Election Results Agent.

This module implements Celery tasks for scraping jobs and export generation,
integrating with the OrchestratorAgent for job state management.

Requirements: 6.3, 6.4, 8.1, 8.2
"""

import asyncio
import csv
import io
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from celery import Task, current_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.agents.orchestrator import (
    JobCheckpoint,
    JobConfig,
    JobProgress,
    JobStatus,
    OrchestratorAgent,
)
from app.config import get_settings
from app.core.aggregator.service import AggregationService
from app.models.election import ElectionResult, ElectionType, PartyResult, PoliticalParty
from app.models.geography import LGA, PollingUnit, State, Ward
from app.models.job import JobLog, ScrapingJob
from app.workers.celery_app import celery_app

logger = logging.getLogger("inec_agent.workers.tasks")

# Get settings
settings = get_settings()

# Create async engine for tasks
_engine = create_async_engine(
    settings.database.async_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

_async_session_factory = async_sessionmaker(
    _engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def run_async(coro):
    """Run an async coroutine in a synchronous context.
    
    Creates a new event loop if one doesn't exist.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


class ScrapingTask(Task):
    """Base task class for scraping jobs with state management."""
    
    _orchestrator: Optional[OrchestratorAgent] = None
    
    @property
    def orchestrator(self) -> OrchestratorAgent:
        """Get or create the orchestrator agent."""
        if self._orchestrator is None:
            self._orchestrator = OrchestratorAgent(
                checkpoint_callback=self._save_checkpoint,
                progress_callback=self._update_progress,
            )
        return self._orchestrator
    
    def _save_checkpoint(self, checkpoint: JobCheckpoint) -> None:
        """Save checkpoint to database."""
        run_async(self._async_save_checkpoint(checkpoint))
    
    async def _async_save_checkpoint(self, checkpoint: JobCheckpoint) -> None:
        """Async implementation of checkpoint saving."""
        async with _async_session_factory() as session:
            try:
                result = await session.execute(
                    select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(checkpoint.job_id))
                )
                job = result.scalar_one_or_none()
                
                if job:
                    job.checkpoint_data = checkpoint.to_dict()
                    job.last_processed_pu = checkpoint.last_processed_pu
                    await session.commit()
                    logger.debug(f"Checkpoint saved for job {checkpoint.job_id}")
            except Exception as e:
                logger.error(f"Failed to save checkpoint: {e}")
                await session.rollback()
    
    def _update_progress(self, progress: JobProgress) -> None:
        """Update task progress state."""
        if current_task:
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "job_id": progress.job_id,
                    "status": progress.status.value,
                    "total_units": progress.total_units,
                    "processed_count": progress.processed_count,
                    "success_count": progress.success_count,
                    "failed_count": progress.failed_count,
                    "progress_percentage": progress.progress_percentage,
                    "estimated_time_remaining": progress.estimated_time_remaining,
                    "current_unit": progress.current_unit,
                },
            )
        
        # Also update database
        run_async(self._async_update_job_progress(progress))
    
    async def _async_update_job_progress(self, progress: JobProgress) -> None:
        """Async implementation of job progress update."""
        async with _async_session_factory() as session:
            try:
                result = await session.execute(
                    select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(progress.job_id))
                )
                job = result.scalar_one_or_none()
                
                if job:
                    job.status = progress.status.value
                    job.processed_count = progress.processed_count
                    job.success_count = progress.success_count
                    job.failed_count = progress.failed_count
                    
                    if progress.status == JobStatus.COMPLETED:
                        job.completed_at = datetime.utcnow()
                    
                    await session.commit()
            except Exception as e:
                logger.error(f"Failed to update job progress: {e}")
                await session.rollback()


@celery_app.task(
    bind=True,
    base=ScrapingTask,
    name="app.workers.tasks.run_scraping_job",
    max_retries=3,
    soft_time_limit=3600,
    time_limit=3900,
)
def run_scraping_job(
    self: ScrapingTask,
    job_id: str,
    election_type: Optional[str] = None,
    target_state: Optional[str] = None,
    target_lga: Optional[str] = None,
    target_ward: Optional[str] = None,
    resume_from_checkpoint: bool = False,
) -> Dict[str, Any]:
    """Run a scraping job with the orchestrator agent.
    
    This task manages the scraping workflow, including:
    - Job state management (start, pause, resume, complete)
    - Progress tracking and checkpointing
    - Integration with the OrchestratorAgent
    
    Args:
        job_id: UUID of the scraping job
        election_type: Target election type filter
        target_state: Target state filter
        target_lga: Target LGA filter
        target_ward: Target ward filter
        resume_from_checkpoint: Whether to resume from a saved checkpoint
        
    Returns:
        Dictionary with job summary
        
    Requirements: 6.3, 6.4
    """
    logger.info(f"Starting scraping job {job_id}")
    
    try:
        return run_async(
            _async_run_scraping_job(
                self,
                job_id,
                election_type,
                target_state,
                target_lga,
                target_ward,
                resume_from_checkpoint,
            )
        )
    except SoftTimeLimitExceeded:
        logger.warning(f"Job {job_id} hit soft time limit, saving checkpoint")
        # Save checkpoint before termination
        run_async(_save_job_state(job_id, JobStatus.PAUSED))
        raise
    except Exception as e:
        logger.error(f"Job {job_id} failed with error: {e}")
        run_async(_save_job_state(job_id, JobStatus.FAILED, str(e)))
        raise


async def _async_run_scraping_job(
    task: ScrapingTask,
    job_id: str,
    election_type: Optional[str],
    target_state: Optional[str],
    target_lga: Optional[str],
    target_ward: Optional[str],
    resume_from_checkpoint: bool,
) -> Dict[str, Any]:
    """Async implementation of the scraping job."""
    async with _async_session_factory() as session:
        # Get or create job record
        result = await session.execute(
            select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"error": "Job not found", "job_id": job_id}
        
        # Update job status to running
        job.status = JobStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        await session.commit()
        
        # Log job start
        log_entry = JobLog(
            job_id=job.id,
            level="INFO",
            message=f"Job started with filters: election_type={election_type}, "
                    f"state={target_state}, lga={target_lga}, ward={target_ward}",
            log_metadata={
                "election_type": election_type,
                "target_state": target_state,
                "target_lga": target_lga,
                "target_ward": target_ward,
                "resume": resume_from_checkpoint,
            },
        )
        session.add(log_entry)
        await session.commit()
        
        # Configure orchestrator
        config = JobConfig(
            election_type=election_type,
            target_state=target_state,
            target_lga=target_lga,
            target_ward=target_ward,
            max_concurrent=settings.scraping.max_concurrent_requests,
        )
        
        orchestrator = task.orchestrator
        orchestrator.config = config
        
        # Resume from checkpoint if requested
        if resume_from_checkpoint and job.checkpoint_data:
            checkpoint = JobCheckpoint.from_dict(job.checkpoint_data)
            await orchestrator.restore_from_checkpoint(checkpoint)
            logger.info(f"Resumed job {job_id} from checkpoint")
        else:
            # Start new job
            await orchestrator.start_job(job_id=job_id)
        
        # Get polling units to process (placeholder - actual implementation
        # would query the portal or database)
        # For now, we'll simulate with an empty list
        # In production, this would integrate with the NavigatorAgent
        polling_units: List[Any] = []
        
        # Update total count
        job.total_polling_units = len(polling_units)
        await session.commit()
        
        # Process polling units (placeholder for actual processing)
        # In production, this would call orchestrator.distribute_work()
        # with actual polling units and processing function
        
        # Mark job as completed
        job.status = JobStatus.COMPLETED.value
        job.completed_at = datetime.utcnow()
        await session.commit()
        
        # Log completion
        log_entry = JobLog(
            job_id=job.id,
            level="INFO",
            message=f"Job completed: {job.success_count} success, {job.failed_count} failed",
            log_metadata={
                "total": job.total_polling_units,
                "processed": job.processed_count,
                "success": job.success_count,
                "failed": job.failed_count,
            },
        )
        session.add(log_entry)
        await session.commit()
        
        return orchestrator.get_summary(job_id)


async def _save_job_state(
    job_id: str,
    status: JobStatus,
    error_message: Optional[str] = None,
) -> None:
    """Save job state to database."""
    async with _async_session_factory() as session:
        try:
            result = await session.execute(
                select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
            )
            job = result.scalar_one_or_none()
            
            if job:
                job.status = status.value
                if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                    job.completed_at = datetime.utcnow()
                
                if error_message:
                    log_entry = JobLog(
                        job_id=job.id,
                        level="ERROR",
                        message=error_message,
                    )
                    session.add(log_entry)
                
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to save job state: {e}")
            await session.rollback()


@celery_app.task(
    bind=True,
    name="app.workers.tasks.generate_csv_export",
    max_retries=3,
    soft_time_limit=600,
    time_limit=660,
)
def generate_csv_export(
    self,
    export_id: str,
    election_type_id: Optional[str] = None,
    state_id: Optional[str] = None,
    lga_id: Optional[str] = None,
    ward_id: Optional[str] = None,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """Generate a CSV export of election results.
    
    This task queries election results based on filters and generates
    a CSV file with the aggregated data.
    
    Args:
        export_id: Unique identifier for this export
        election_type_id: Filter by election type UUID
        state_id: Filter by state UUID
        lga_id: Filter by LGA UUID
        ward_id: Filter by ward UUID
        include_metadata: Whether to include metadata in export
        
    Returns:
        Dictionary with export file path and record count
        
    Requirements: 8.1, 8.3
    """
    logger.info(f"Starting CSV export {export_id}")
    
    try:
        return run_async(
            _async_generate_csv_export(
                export_id,
                election_type_id,
                state_id,
                lga_id,
                ward_id,
                include_metadata,
            )
        )
    except Exception as e:
        logger.error(f"CSV export {export_id} failed: {e}")
        raise self.retry(exc=e, countdown=60)


async def _async_generate_csv_export(
    export_id: str,
    election_type_id: Optional[str],
    state_id: Optional[str],
    lga_id: Optional[str],
    ward_id: Optional[str],
    include_metadata: bool,
) -> Dict[str, Any]:
    """Async implementation of CSV export generation."""
    async with _async_session_factory() as session:
        # Build query with filters
        query = (
            select(
                ElectionResult,
                PollingUnit.name.label("polling_unit_name"),
                PollingUnit.code.label("polling_unit_code"),
                Ward.name.label("ward_name"),
                LGA.name.label("lga_name"),
                State.name.label("state_name"),
                ElectionType.name.label("election_type_name"),
                ElectionType.code.label("election_type_code"),
            )
            .join(PollingUnit, ElectionResult.polling_unit_id == PollingUnit.id)
            .join(Ward, PollingUnit.ward_id == Ward.id)
            .join(LGA, Ward.lga_id == LGA.id)
            .join(State, LGA.state_id == State.id)
            .join(ElectionType, ElectionResult.election_type_id == ElectionType.id)
        )
        
        # Apply filters
        if election_type_id:
            query = query.where(ElectionResult.election_type_id == uuid.UUID(election_type_id))
        if state_id:
            query = query.where(State.id == uuid.UUID(state_id))
        if lga_id:
            query = query.where(LGA.id == uuid.UUID(lga_id))
        if ward_id:
            query = query.where(Ward.id == uuid.UUID(ward_id))
        
        result = await session.execute(query)
        rows = result.fetchall()
        
        # Generate CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = [
            "election_type",
            "state",
            "lga",
            "ward",
            "polling_unit",
            "polling_unit_code",
            "accredited_voters",
            "valid_votes",
            "rejected_votes",
            "confidence_score",
        ]
        
        if include_metadata:
            headers.extend(["extracted_at", "source_image_path"])
        
        # Add party columns dynamically
        # First, get all unique parties
        party_query = select(PoliticalParty.code).order_by(PoliticalParty.code)
        party_result = await session.execute(party_query)
        party_codes = [row[0] for row in party_result.fetchall()]
        headers.extend(party_codes)
        
        writer.writerow(headers)
        
        # Write data rows
        record_count = 0
        for row in rows:
            election_result = row[0]
            
            # Get party results for this election result
            party_results_query = (
                select(PartyResult, PoliticalParty.code)
                .join(PoliticalParty, PartyResult.party_id == PoliticalParty.id)
                .where(PartyResult.election_result_id == election_result.id)
            )
            party_results = await session.execute(party_results_query)
            party_votes = {pr[1]: pr[0].vote_count for pr in party_results.fetchall()}
            
            # Build row data
            row_data = [
                row.election_type_code,
                row.state_name,
                row.lga_name,
                row.ward_name,
                row.polling_unit_name,
                row.polling_unit_code,
                election_result.accredited_voters,
                election_result.valid_votes,
                election_result.rejected_votes,
                float(election_result.confidence_score),
            ]
            
            if include_metadata:
                row_data.extend([
                    election_result.extracted_at.isoformat() if election_result.extracted_at else "",
                    election_result.source_image_path or "",
                ])
            
            # Add party vote counts
            for party_code in party_codes:
                row_data.append(party_votes.get(party_code, 0))
            
            writer.writerow(row_data)
            record_count += 1
        
        # Save to file
        export_dir = os.path.join(settings.scraping.storage_path, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        file_path = os.path.join(export_dir, f"{export_id}.csv")
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            f.write(output.getvalue())
        
        logger.info(f"CSV export {export_id} completed with {record_count} records")
        
        return {
            "export_id": export_id,
            "format": "csv",
            "file_path": file_path,
            "record_count": record_count,
            "generated_at": datetime.utcnow().isoformat(),
            "filters": {
                "election_type_id": election_type_id,
                "state_id": state_id,
                "lga_id": lga_id,
                "ward_id": ward_id,
            },
        }


@celery_app.task(
    bind=True,
    name="app.workers.tasks.generate_json_export",
    max_retries=3,
    soft_time_limit=600,
    time_limit=660,
)
def generate_json_export(
    self,
    export_id: str,
    election_type_id: Optional[str] = None,
    state_id: Optional[str] = None,
    lga_id: Optional[str] = None,
    ward_id: Optional[str] = None,
    include_metadata: bool = True,
    aggregation_level: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a JSON export of election results.
    
    This task queries election results based on filters and generates
    a JSON file with the data, optionally aggregated at ward/LGA level.
    
    Args:
        export_id: Unique identifier for this export
        election_type_id: Filter by election type UUID
        state_id: Filter by state UUID
        lga_id: Filter by LGA UUID
        ward_id: Filter by ward UUID
        include_metadata: Whether to include metadata in export
        aggregation_level: Optional aggregation level ('ward', 'lga', 'state')
        
    Returns:
        Dictionary with export file path and record count
        
    Requirements: 8.2, 8.3, 8.4
    """
    logger.info(f"Starting JSON export {export_id}")
    
    try:
        return run_async(
            _async_generate_json_export(
                export_id,
                election_type_id,
                state_id,
                lga_id,
                ward_id,
                include_metadata,
                aggregation_level,
            )
        )
    except Exception as e:
        logger.error(f"JSON export {export_id} failed: {e}")
        raise self.retry(exc=e, countdown=60)


async def _async_generate_json_export(
    export_id: str,
    election_type_id: Optional[str],
    state_id: Optional[str],
    lga_id: Optional[str],
    ward_id: Optional[str],
    include_metadata: bool,
    aggregation_level: Optional[str],
) -> Dict[str, Any]:
    """Async implementation of JSON export generation."""
    async with _async_session_factory() as session:
        export_data: Dict[str, Any] = {
            "export_id": export_id,
            "format": "json",
            "generated_at": datetime.utcnow().isoformat(),
            "filters": {
                "election_type_id": election_type_id,
                "state_id": state_id,
                "lga_id": lga_id,
                "ward_id": ward_id,
            },
        }
        
        if aggregation_level:
            # Generate aggregated export
            export_data["aggregation_level"] = aggregation_level
            export_data["results"] = await _generate_aggregated_results(
                session,
                election_type_id,
                state_id,
                lga_id,
                ward_id,
                aggregation_level,
            )
        else:
            # Generate detailed export
            export_data["results"] = await _generate_detailed_results(
                session,
                election_type_id,
                state_id,
                lga_id,
                ward_id,
                include_metadata,
            )
        
        export_data["record_count"] = len(export_data["results"])
        
        # Save to file
        export_dir = os.path.join(settings.scraping.storage_path, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        file_path = os.path.join(export_dir, f"{export_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"JSON export {export_id} completed with {export_data['record_count']} records")
        
        return {
            "export_id": export_id,
            "format": "json",
            "file_path": file_path,
            "record_count": export_data["record_count"],
            "generated_at": export_data["generated_at"],
            "filters": export_data["filters"],
        }


async def _generate_detailed_results(
    session: AsyncSession,
    election_type_id: Optional[str],
    state_id: Optional[str],
    lga_id: Optional[str],
    ward_id: Optional[str],
    include_metadata: bool,
) -> List[Dict[str, Any]]:
    """Generate detailed (non-aggregated) results for JSON export."""
    # Build query with filters
    query = (
        select(
            ElectionResult,
            PollingUnit.name.label("polling_unit_name"),
            PollingUnit.code.label("polling_unit_code"),
            Ward.name.label("ward_name"),
            Ward.id.label("ward_id"),
            LGA.name.label("lga_name"),
            LGA.id.label("lga_id"),
            State.name.label("state_name"),
            State.id.label("state_id"),
            ElectionType.name.label("election_type_name"),
            ElectionType.code.label("election_type_code"),
        )
        .join(PollingUnit, ElectionResult.polling_unit_id == PollingUnit.id)
        .join(Ward, PollingUnit.ward_id == Ward.id)
        .join(LGA, Ward.lga_id == LGA.id)
        .join(State, LGA.state_id == State.id)
        .join(ElectionType, ElectionResult.election_type_id == ElectionType.id)
    )
    
    # Apply filters
    if election_type_id:
        query = query.where(ElectionResult.election_type_id == uuid.UUID(election_type_id))
    if state_id:
        query = query.where(State.id == uuid.UUID(state_id))
    if lga_id:
        query = query.where(LGA.id == uuid.UUID(lga_id))
    if ward_id:
        query = query.where(Ward.id == uuid.UUID(ward_id))
    
    result = await session.execute(query)
    rows = result.fetchall()
    
    results: List[Dict[str, Any]] = []
    
    for row in rows:
        election_result = row[0]
        
        # Get party results
        party_results_query = (
            select(PartyResult, PoliticalParty.name, PoliticalParty.code)
            .join(PoliticalParty, PartyResult.party_id == PoliticalParty.id)
            .where(PartyResult.election_result_id == election_result.id)
        )
        party_results = await session.execute(party_results_query)
        
        party_votes = [
            {
                "party_name": pr[1],
                "party_code": pr[2],
                "vote_count": pr[0].vote_count,
                "percentage": float(pr[0].percentage),
            }
            for pr in party_results.fetchall()
        ]
        
        result_data: Dict[str, Any] = {
            "id": str(election_result.id),
            "election_type": {
                "name": row.election_type_name,
                "code": row.election_type_code,
            },
            "location": {
                "state": {"id": str(row.state_id), "name": row.state_name},
                "lga": {"id": str(row.lga_id), "name": row.lga_name},
                "ward": {"id": str(row.ward_id), "name": row.ward_name},
                "polling_unit": {
                    "id": str(election_result.polling_unit_id),
                    "name": row.polling_unit_name,
                    "code": row.polling_unit_code,
                },
            },
            "votes": {
                "accredited_voters": election_result.accredited_voters,
                "valid_votes": election_result.valid_votes,
                "rejected_votes": election_result.rejected_votes,
            },
            "party_results": party_votes,
            "confidence_score": float(election_result.confidence_score),
        }
        
        if include_metadata:
            result_data["metadata"] = {
                "extracted_at": election_result.extracted_at.isoformat() if election_result.extracted_at else None,
                "source_image_path": election_result.source_image_path,
                "created_at": election_result.created_at.isoformat() if election_result.created_at else None,
            }
        
        results.append(result_data)
    
    return results


async def _generate_aggregated_results(
    session: AsyncSession,
    election_type_id: Optional[str],
    state_id: Optional[str],
    lga_id: Optional[str],
    ward_id: Optional[str],
    aggregation_level: str,
) -> List[Dict[str, Any]]:
    """Generate aggregated results for JSON export."""
    aggregation_service = AggregationService(session)
    results: List[Dict[str, Any]] = []
    
    if not election_type_id:
        # Need election type for aggregation
        return results
    
    election_type_uuid = uuid.UUID(election_type_id)
    
    if aggregation_level == "ward" and ward_id:
        # Single ward aggregation
        agg_result = await aggregation_service.aggregate_ward(
            uuid.UUID(ward_id), election_type_uuid
        )
        if agg_result:
            results.append(_aggregation_to_dict(agg_result))
    
    elif aggregation_level == "lga" and lga_id:
        # Single LGA aggregation
        agg_result = await aggregation_service.aggregate_lga(
            uuid.UUID(lga_id), election_type_uuid
        )
        if agg_result:
            results.append(_aggregation_to_dict(agg_result))
    
    elif aggregation_level == "state" and state_id:
        # Single state aggregation
        agg_result = await aggregation_service.aggregate_state(
            uuid.UUID(state_id), election_type_uuid
        )
        if agg_result:
            results.append(_aggregation_to_dict(agg_result))
    
    elif aggregation_level == "ward":
        # All wards in scope
        ward_query = select(Ward.id)
        if lga_id:
            ward_query = ward_query.where(Ward.lga_id == uuid.UUID(lga_id))
        elif state_id:
            ward_query = ward_query.join(LGA, Ward.lga_id == LGA.id).where(
                LGA.state_id == uuid.UUID(state_id)
            )
        
        ward_result = await session.execute(ward_query)
        ward_ids = [row[0] for row in ward_result.fetchall()]
        
        for w_id in ward_ids:
            agg_result = await aggregation_service.aggregate_ward(w_id, election_type_uuid)
            if agg_result:
                results.append(_aggregation_to_dict(agg_result))
    
    elif aggregation_level == "lga":
        # All LGAs in scope
        lga_query = select(LGA.id)
        if state_id:
            lga_query = lga_query.where(LGA.state_id == uuid.UUID(state_id))
        
        lga_result = await session.execute(lga_query)
        lga_ids = [row[0] for row in lga_result.fetchall()]
        
        for l_id in lga_ids:
            agg_result = await aggregation_service.aggregate_lga(l_id, election_type_uuid)
            if agg_result:
                results.append(_aggregation_to_dict(agg_result))
    
    return results


def _aggregation_to_dict(agg_result) -> Dict[str, Any]:
    """Convert AggregationResult to dictionary."""
    return {
        "level": agg_result.level,
        "location": {
            "id": str(agg_result.location_id),
            "name": agg_result.location_name,
        },
        "election_type": {
            "id": str(agg_result.election_type_id),
            "code": agg_result.election_type_code,
        },
        "totals": {
            "valid_votes": agg_result.total_valid_votes,
            "accredited_voters": agg_result.total_accredited_voters,
            "rejected_votes": agg_result.total_rejected_votes,
        },
        "polling_units": {
            "total": agg_result.total_polling_units,
            "processed": agg_result.processed_polling_units,
            "flagged": agg_result.flagged_polling_units,
        },
        "party_results": [
            {
                "party_id": str(pr.party_id),
                "party_name": pr.party_name,
                "party_code": pr.party_code,
                "total_votes": pr.total_votes,
                "percentage": float(pr.percentage),
                "rank": pr.rank,
            }
            for pr in agg_result.party_results
        ],
    }


@celery_app.task(
    name="app.workers.tasks.pause_scraping_job",
)
def pause_scraping_job(job_id: str) -> Dict[str, Any]:
    """Pause a running scraping job.
    
    Args:
        job_id: UUID of the job to pause
        
    Returns:
        Dictionary with pause status
        
    Requirements: 6.3
    """
    logger.info(f"Pausing job {job_id}")
    return run_async(_async_pause_job(job_id))


async def _async_pause_job(job_id: str) -> Dict[str, Any]:
    """Async implementation of job pause."""
    async with _async_session_factory() as session:
        result = await session.execute(
            select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return {"success": False, "error": "Job not found"}
        
        if job.status != JobStatus.RUNNING.value:
            return {"success": False, "error": f"Job is not running (status: {job.status})"}
        
        job.status = JobStatus.PAUSED.value
        
        log_entry = JobLog(
            job_id=job.id,
            level="INFO",
            message="Job paused by user request",
        )
        session.add(log_entry)
        await session.commit()
        
        return {"success": True, "job_id": job_id, "status": JobStatus.PAUSED.value}


@celery_app.task(
    name="app.workers.tasks.resume_scraping_job",
)
def resume_scraping_job(job_id: str) -> Dict[str, Any]:
    """Resume a paused scraping job.
    
    Args:
        job_id: UUID of the job to resume
        
    Returns:
        Dictionary with resume status
        
    Requirements: 6.3, 6.4
    """
    logger.info(f"Resuming job {job_id}")
    return run_async(_async_resume_job(job_id))


async def _async_resume_job(job_id: str) -> Dict[str, Any]:
    """Async implementation of job resume."""
    async with _async_session_factory() as session:
        result = await session.execute(
            select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return {"success": False, "error": "Job not found"}
        
        if job.status != JobStatus.PAUSED.value:
            return {"success": False, "error": f"Job is not paused (status: {job.status})"}
        
        # Queue a new task to resume the job
        task = run_scraping_job.delay(
            job_id=job_id,
            election_type=job.election_type,
            target_state=job.target_state,
            target_lga=job.target_lga,
            target_ward=job.target_ward,
            resume_from_checkpoint=True,
        )
        
        log_entry = JobLog(
            job_id=job.id,
            level="INFO",
            message=f"Job resumed with task {task.id}",
        )
        session.add(log_entry)
        await session.commit()
        
        return {
            "success": True,
            "job_id": job_id,
            "task_id": task.id,
            "status": "resuming",
        }


@celery_app.task(
    name="app.workers.tasks.cancel_scraping_job",
)
def cancel_scraping_job(job_id: str) -> Dict[str, Any]:
    """Cancel a running or paused scraping job.
    
    Args:
        job_id: UUID of the job to cancel
        
    Returns:
        Dictionary with cancellation status
        
    Requirements: 6.3
    """
    logger.info(f"Cancelling job {job_id}")
    return run_async(_async_cancel_job(job_id))


async def _async_cancel_job(job_id: str) -> Dict[str, Any]:
    """Async implementation of job cancellation."""
    async with _async_session_factory() as session:
        result = await session.execute(
            select(ScrapingJob).where(ScrapingJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return {"success": False, "error": "Job not found"}
        
        if job.status not in (JobStatus.RUNNING.value, JobStatus.PAUSED.value, JobStatus.QUEUED.value):
            return {"success": False, "error": f"Job cannot be cancelled (status: {job.status})"}
        
        job.status = JobStatus.CANCELLED.value
        job.completed_at = datetime.utcnow()
        
        log_entry = JobLog(
            job_id=job.id,
            level="INFO",
            message="Job cancelled by user request",
        )
        session.add(log_entry)
        await session.commit()
        
        return {"success": True, "job_id": job_id, "status": JobStatus.CANCELLED.value}
