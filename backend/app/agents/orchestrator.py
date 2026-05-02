"""Orchestrator agent for coordinating election data processing.

This module provides the central coordinator that manages the scraping
workflow, distributes work across agents, and handles job state.

Requirements: 6.3, 6.4, 7.4
"""
from __future__ import annotations


import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.core.scraper.navigator import PollingUnit

logger = logging.getLogger("inec_agent.agents.orchestrator")


class JobStatus(str, Enum):
    """Status of a scraping job."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobCheckpoint:
    """Checkpoint data for job resumption.
    
    Attributes:
        job_id: Job identifier
        last_processed_pu: Last successfully processed polling unit
        processed_units: Set of processed polling unit IDs
        pending_units: List of pending polling unit IDs
        failed_units: List of failed polling unit IDs
        timestamp: Checkpoint creation timestamp
    """

    job_id: str
    last_processed_pu: str | None = None
    processed_units: set = field(default_factory=set)
    pending_units: list[str] = field(default_factory=list)
    failed_units: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary for storage."""
        return {
            "job_id": self.job_id,
            "last_processed_pu": self.last_processed_pu,
            "processed_units": list(self.processed_units),
            "pending_units": self.pending_units,
            "failed_units": self.failed_units,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobCheckpoint":
        """Create checkpoint from dictionary."""
        return cls(
            job_id=data["job_id"],
            last_processed_pu=data.get("last_processed_pu"),
            processed_units=set(data.get("processed_units", [])),
            pending_units=data.get("pending_units", []),
            failed_units=data.get("failed_units", []),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
        )


@dataclass
class JobProgress:
    """Progress information for a scraping job.
    
    Attributes:
        job_id: Job identifier
        status: Current job status
        total_units: Total polling units to process
        processed_count: Number of processed units
        success_count: Number of successfully processed units
        failed_count: Number of failed units
        progress_percentage: Completion percentage
        estimated_time_remaining: Estimated seconds remaining
        current_unit: Currently processing unit
    """

    job_id: str
    status: JobStatus
    total_units: int = 0
    processed_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    progress_percentage: float = 0.0
    estimated_time_remaining: int | None = None
    current_unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert progress to dictionary."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "total_units": self.total_units,
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "progress_percentage": self.progress_percentage,
            "estimated_time_remaining": self.estimated_time_remaining,
            "current_unit": self.current_unit,
        }


@dataclass
class JobConfig:
    """Configuration for a scraping job.
    
    Attributes:
        election_type: Target election type (None = all)
        target_state: Target state (None = all)
        target_lga: Target LGA (None = all)
        target_ward: Target ward (None = all)
        checkpoint_interval: Save checkpoint every N units
        failure_threshold: Flag job if failure rate exceeds this
        max_concurrent: Maximum concurrent processing tasks
    """

    election_type: str | None = None
    target_state: str | None = None
    target_lga: str | None = None
    target_ward: str | None = None
    checkpoint_interval: int = 100
    failure_threshold: float = 0.1
    max_concurrent: int = 5


class OrchestratorAgent:
    """Central coordinator for the scraping workflow.
    
    This agent manages:
    - Work distribution across navigator and processor agents
    - Progress monitoring and status updates
    - Failure handling and retry logic
    - Job state persistence and checkpoints
    - Pause/resume functionality
    
    Requirements: 6.3, 6.4, 7.4
    """

    def __init__(
        self,
        config: JobConfig | None = None,
        checkpoint_callback: Callable[[JobCheckpoint], None] | None = None,
        progress_callback: Callable[[JobProgress], None] | None = None,
    ):
        """Initialize the orchestrator agent.
        
        Args:
            config: Job configuration
            checkpoint_callback: Callback for checkpoint persistence
            progress_callback: Callback for progress updates
        """
        self.config = config or JobConfig()
        self.checkpoint_callback = checkpoint_callback
        self.progress_callback = progress_callback

        # Job state
        self._jobs: dict[str, JobProgress] = {}
        self._checkpoints: dict[str, JobCheckpoint] = {}
        self._pause_events: dict[str, asyncio.Event] = {}
        self._cancel_flags: dict[str, bool] = {}

        # Processing state
        self._processing_tasks: dict[str, list[asyncio.Task]] = {}
        self._start_times: dict[str, datetime] = {}

        logger.info("OrchestratorAgent initialized")

    async def start_job(
        self,
        job_id: str | None = None,
        polling_units: list[PollingUnit] | None = None,
        config: JobConfig | None = None,
    ) -> str:
        """Start a new scraping job.
        
        Args:
            job_id: Optional job ID (generated if not provided)
            polling_units: List of polling units to process
            config: Optional job-specific configuration
            
        Returns:
            Job ID
        """
        job_id = job_id or str(uuid.uuid4())
        job_config = config or self.config

        logger.info(f"Starting job {job_id}")

        # Initialize job state
        total_units = len(polling_units) if polling_units else 0

        self._jobs[job_id] = JobProgress(
            job_id=job_id,
            status=JobStatus.QUEUED,
            total_units=total_units,
        )

        self._checkpoints[job_id] = JobCheckpoint(
            job_id=job_id,
            pending_units=[pu.id for pu in polling_units] if polling_units else [],
        )

        self._pause_events[job_id] = asyncio.Event()
        self._pause_events[job_id].set()  # Not paused initially

        self._cancel_flags[job_id] = False
        self._start_times[job_id] = datetime.utcnow()

        # Update status to running
        self._jobs[job_id].status = JobStatus.RUNNING

        # Notify progress
        self._notify_progress(job_id)

        return job_id

    async def process_unit(
        self,
        job_id: str,
        polling_unit: PollingUnit,
        process_func: Callable[[PollingUnit], Any],
    ) -> bool:
        """Process a single polling unit.
        
        Args:
            job_id: Job identifier
            polling_unit: Polling unit to process
            process_func: Function to process the unit
            
        Returns:
            True if successful, False otherwise
        """
        # Check for pause
        await self._pause_events[job_id].wait()

        # Check for cancellation
        if self._cancel_flags.get(job_id, False):
            logger.info(f"Job {job_id} cancelled, skipping unit {polling_unit.id}")
            return False

        # Update current unit
        self._jobs[job_id].current_unit = polling_unit.id

        try:
            logger.debug(f"Processing unit {polling_unit.id} for job {job_id}")

            # Execute the processing function
            await process_func(polling_unit)

            # Update success count
            self._jobs[job_id].success_count += 1
            self._checkpoints[job_id].processed_units.add(polling_unit.id)
            self._checkpoints[job_id].last_processed_pu = polling_unit.id

            return True

        except Exception as e:
            logger.error(f"Failed to process unit {polling_unit.id}: {e}")

            # Update failure count
            self._jobs[job_id].failed_count += 1
            self._checkpoints[job_id].failed_units.append(polling_unit.id)

            return False

        finally:
            # Update processed count
            self._jobs[job_id].processed_count += 1

            # Remove from pending
            if polling_unit.id in self._checkpoints[job_id].pending_units:
                self._checkpoints[job_id].pending_units.remove(polling_unit.id)

            # Update progress
            self._update_progress(job_id)

            # Save checkpoint if interval reached
            if self._jobs[job_id].processed_count % self.config.checkpoint_interval == 0:
                await self._save_checkpoint(job_id)

    async def distribute_work(
        self,
        job_id: str,
        polling_units: list[PollingUnit],
        process_func: Callable[[PollingUnit], Any],
    ) -> None:
        """Distribute polling units across processing tasks.
        
        Args:
            job_id: Job identifier
            polling_units: List of polling units to process
            process_func: Function to process each unit
        """
        logger.info(f"Distributing {len(polling_units)} units for job {job_id}")

        # Filter out already processed units (for resume)
        checkpoint = self._checkpoints.get(job_id)
        if checkpoint:
            polling_units = [
                pu for pu in polling_units
                if pu.id not in checkpoint.processed_units
            ]
            logger.info(f"After filtering processed units: {len(polling_units)} remaining")

        # Process units with concurrency limit
        semaphore = asyncio.Semaphore(self.config.max_concurrent)

        async def process_with_semaphore(pu: PollingUnit) -> bool:
            async with semaphore:
                return await self.process_unit(job_id, pu, process_func)

        # Create tasks for all units
        tasks = [
            asyncio.create_task(process_with_semaphore(pu))
            for pu in polling_units
        ]

        self._processing_tasks[job_id] = tasks

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check failure threshold
        failure_rate = self._jobs[job_id].failed_count / max(self._jobs[job_id].processed_count, 1)
        if failure_rate > self.config.failure_threshold:
            logger.warning(f"Job {job_id} failure rate ({failure_rate:.2%}) exceeds threshold")

        # Update job status
        if self._cancel_flags.get(job_id, False):
            self._jobs[job_id].status = JobStatus.CANCELLED
        elif self._jobs[job_id].failed_count == self._jobs[job_id].total_units:
            self._jobs[job_id].status = JobStatus.FAILED
        else:
            self._jobs[job_id].status = JobStatus.COMPLETED

        # Final checkpoint
        await self._save_checkpoint(job_id)

        # Notify completion
        self._notify_progress(job_id)

        logger.info(
            f"Job {job_id} completed: {self._jobs[job_id].success_count} success, "
            f"{self._jobs[job_id].failed_count} failed"
        )

    async def pause_job(self, job_id: str) -> bool:
        """Pause a running job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if paused successfully
        """
        if job_id not in self._jobs:
            logger.warning(f"Job {job_id} not found")
            return False

        if self._jobs[job_id].status != JobStatus.RUNNING:
            logger.warning(f"Job {job_id} is not running, cannot pause")
            return False

        logger.info(f"Pausing job {job_id}")

        # Clear the pause event to block processing
        self._pause_events[job_id].clear()
        self._jobs[job_id].status = JobStatus.PAUSED

        # Save checkpoint
        await self._save_checkpoint(job_id)

        self._notify_progress(job_id)

        return True

    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if resumed successfully
        """
        if job_id not in self._jobs:
            logger.warning(f"Job {job_id} not found")
            return False

        if self._jobs[job_id].status != JobStatus.PAUSED:
            logger.warning(f"Job {job_id} is not paused, cannot resume")
            return False

        logger.info(f"Resuming job {job_id}")

        # Set the pause event to allow processing
        self._pause_events[job_id].set()
        self._jobs[job_id].status = JobStatus.RUNNING

        self._notify_progress(job_id)

        return True

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running or paused job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled successfully
        """
        if job_id not in self._jobs:
            logger.warning(f"Job {job_id} not found")
            return False

        if self._jobs[job_id].status not in (JobStatus.RUNNING, JobStatus.PAUSED):
            logger.warning(f"Job {job_id} cannot be cancelled in status {self._jobs[job_id].status}")
            return False

        logger.info(f"Cancelling job {job_id}")

        # Set cancel flag
        self._cancel_flags[job_id] = True

        # Resume if paused (to allow tasks to check cancel flag)
        if self._jobs[job_id].status == JobStatus.PAUSED:
            self._pause_events[job_id].set()

        # Cancel any pending tasks
        if job_id in self._processing_tasks:
            for task in self._processing_tasks[job_id]:
                if not task.done():
                    task.cancel()

        self._jobs[job_id].status = JobStatus.CANCELLED

        # Save final checkpoint
        await self._save_checkpoint(job_id)

        self._notify_progress(job_id)

        return True

    def get_job_progress(self, job_id: str) -> JobProgress | None:
        """Get progress information for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobProgress or None if not found
        """
        return self._jobs.get(job_id)

    def get_job_checkpoint(self, job_id: str) -> JobCheckpoint | None:
        """Get checkpoint data for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobCheckpoint or None if not found
        """
        return self._checkpoints.get(job_id)

    async def restore_from_checkpoint(
        self,
        checkpoint: JobCheckpoint,
    ) -> str:
        """Restore a job from a checkpoint.
        
        Args:
            checkpoint: Checkpoint data to restore from
            
        Returns:
            Job ID
        """
        job_id = checkpoint.job_id

        logger.info(f"Restoring job {job_id} from checkpoint")

        # Restore checkpoint
        self._checkpoints[job_id] = checkpoint

        # Calculate progress
        processed = len(checkpoint.processed_units)
        failed = len(checkpoint.failed_units)
        pending = len(checkpoint.pending_units)
        total = processed + pending

        # Initialize job progress
        self._jobs[job_id] = JobProgress(
            job_id=job_id,
            status=JobStatus.QUEUED,
            total_units=total,
            processed_count=processed,
            success_count=processed - failed,
            failed_count=failed,
            progress_percentage=(processed / total * 100) if total > 0 else 0,
        )

        # Initialize control events
        self._pause_events[job_id] = asyncio.Event()
        self._pause_events[job_id].set()
        self._cancel_flags[job_id] = False

        return job_id

    async def handle_failure(
        self,
        job_id: str,
        polling_unit: PollingUnit,
        error: Exception,
    ) -> None:
        """Handle a processing failure.
        
        Args:
            job_id: Job identifier
            polling_unit: Failed polling unit
            error: Exception that occurred
        """
        logger.error(
            f"Handling failure for unit {polling_unit.id} in job {job_id}: {error}"
        )

        # Add to failed units
        if job_id in self._checkpoints:
            self._checkpoints[job_id].failed_units.append(polling_unit.id)

        # Check if we should stop the job
        if job_id in self._jobs:
            failure_rate = self._jobs[job_id].failed_count / max(self._jobs[job_id].processed_count, 1)
            if failure_rate > self.config.failure_threshold:
                logger.warning(
                    f"Job {job_id} failure rate ({failure_rate:.2%}) exceeds threshold, "
                    "consider pausing for review"
                )

    def get_summary(self, job_id: str) -> dict[str, Any]:
        """Get summary report for a completed job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Summary dictionary
        """
        progress = self._jobs.get(job_id)
        checkpoint = self._checkpoints.get(job_id)

        if not progress:
            return {"error": "Job not found"}

        start_time = self._start_times.get(job_id)
        duration = None
        if start_time:
            duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            "job_id": job_id,
            "status": progress.status.value,
            "total_polling_units": progress.total_units,
            "processed": progress.processed_count,
            "successful": progress.success_count,
            "failed": progress.failed_count,
            "success_rate": (progress.success_count / max(progress.processed_count, 1)) * 100,
            "failure_rate": (progress.failed_count / max(progress.processed_count, 1)) * 100,
            "duration_seconds": duration,
            "failed_units": checkpoint.failed_units if checkpoint else [],
        }

    def _update_progress(self, job_id: str) -> None:
        """Update progress calculations for a job.
        
        Args:
            job_id: Job identifier
        """
        progress = self._jobs.get(job_id)
        if not progress:
            return

        # Calculate percentage
        if progress.total_units > 0:
            progress.progress_percentage = (
                progress.processed_count / progress.total_units * 100
            )

        # Estimate time remaining
        start_time = self._start_times.get(job_id)
        if start_time and progress.processed_count > 0:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            rate = progress.processed_count / elapsed
            remaining = progress.total_units - progress.processed_count
            if rate > 0:
                progress.estimated_time_remaining = int(remaining / rate)

    def _notify_progress(self, job_id: str) -> None:
        """Notify progress callback if configured.
        
        Args:
            job_id: Job identifier
        """
        if self.progress_callback and job_id in self._jobs:
            try:
                self.progress_callback(self._jobs[job_id])
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")

    async def _save_checkpoint(self, job_id: str) -> None:
        """Save checkpoint for a job.
        
        Args:
            job_id: Job identifier
        """
        checkpoint = self._checkpoints.get(job_id)
        if not checkpoint:
            return

        checkpoint.timestamp = datetime.utcnow()

        if self.checkpoint_callback:
            try:
                self.checkpoint_callback(checkpoint)
                logger.debug(f"Checkpoint saved for job {job_id}")
            except Exception as e:
                logger.error(f"Failed to save checkpoint: {e}")
