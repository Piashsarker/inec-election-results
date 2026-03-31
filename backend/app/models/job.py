"""SQLAlchemy models for job management.

This module defines the job-related models: ScrapingJob, JobLog, and FlaggedResult.

Requirements: 4.1, 4.3, 4.5
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.election import ElectionResult


class ScrapingJob(BaseModel):
    """Model representing a scraping job.
    
    Tracks scraping job state for pause/resume functionality and progress monitoring.
    
    Attributes:
        id: UUID primary key
        status: Job status (queued, running, paused, completed, failed, cancelled)
        election_type: Target election type filter (None = all types)
        target_state: Target state filter (None = all states)
        target_lga: Target LGA filter (None = all LGAs)
        target_ward: Target ward filter (None = all wards)
        total_polling_units: Total number of polling units to process
        processed_count: Number of polling units processed
        success_count: Number of successfully processed polling units
        failed_count: Number of failed polling units
        last_processed_pu: Identifier of last processed polling unit
        checkpoint_data: JSON data for resuming job
        created_at: Timestamp when job was created
        started_at: Timestamp when job started running
        completed_at: Timestamp when job completed
        logs: Relationship to JobLog records
    """

    __tablename__ = "scraping_jobs"

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
        index=True,
    )
    election_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    target_state: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    target_lga: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    target_ward: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    total_polling_units: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    processed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    success_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    failed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_processed_pu: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    checkpoint_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    logs: Mapped[List["JobLog"]] = relationship(
        "JobLog",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ScrapingJob(id={self.id}, status='{self.status}', processed={self.processed_count}/{self.total_polling_units})>"


class JobLog(BaseModel):
    """Model representing a log entry for a scraping job.
    
    Stores log messages with severity levels and optional metadata.
    
    Attributes:
        id: UUID primary key
        job_id: Foreign key to scraping job
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        message: Log message text
        metadata: Optional JSON metadata
        created_at: Timestamp when log was created
        job: Relationship to ScrapingJob
    """

    __tablename__ = "job_logs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scraping_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    log_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",  # Keep the database column name as 'metadata'
        JSONB,
        nullable=True,
    )

    # Relationships
    job: Mapped["ScrapingJob"] = relationship(
        "ScrapingJob",
        back_populates="logs",
    )

    __table_args__ = (Index("idx_job_logs_job", "job_id"),)

    def __repr__(self) -> str:
        return f"<JobLog(id={self.id}, job_id={self.job_id}, level='{self.level}')>"


class FlaggedResult(BaseModel):
    """Model representing a flagged election result for manual review.
    
    Stores information about results that failed validation or need manual review.
    
    Attributes:
        id: UUID primary key
        election_result_id: Foreign key to election result
        reason: Reason for flagging (e.g., "vote_sum_mismatch", "low_confidence")
        status: Review status (pending, reviewed, resolved)
        review_notes: Optional JSON notes from reviewer
        created_at: Timestamp when flag was created
        reviewed_at: Timestamp when flag was reviewed
        election_result: Relationship to ElectionResult
    """

    __tablename__ = "flagged_results"

    election_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("election_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
    )
    review_notes: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    election_result: Mapped["ElectionResult"] = relationship(
        "ElectionResult",
        back_populates="flagged_results",
    )

    __table_args__ = (
        Index("idx_flagged_results_election", "election_result_id"),
        Index("idx_flagged_results_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<FlaggedResult(id={self.id}, election_result_id={self.election_result_id}, status='{self.status}')>"
