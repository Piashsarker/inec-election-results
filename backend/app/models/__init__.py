"""SQLAlchemy models for database entities.

This module exports all database models for the INEC Election Results Agent.
"""

from app.models.base import Base, BaseModel, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.election import (
    ElectionResult,
    ElectionType,
    PartyResult,
    PoliticalParty,
)
from app.models.geography import LGA, PollingUnit, State, Ward
from app.models.job import FlaggedResult, JobLog, ScrapingJob

__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    # Geographic hierarchy models
    "State",
    "LGA",
    "Ward",
    "PollingUnit",
    # Election models
    "ElectionType",
    "PoliticalParty",
    "ElectionResult",
    "PartyResult",
    # Job management models
    "ScrapingJob",
    "JobLog",
    "FlaggedResult",
]
