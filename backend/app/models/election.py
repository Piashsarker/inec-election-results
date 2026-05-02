"""SQLAlchemy models for election data.

This module defines the election-related models: ElectionType, PoliticalParty,
ElectionResult, and PartyResult.

Requirements: 4.1, 4.3, 4.5
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.geography import PollingUnit
    from app.models.job import FlaggedResult


class ElectionType(BaseModel):
    """Model representing a type of election.

    Election types include Presidential, Governorship, Senatorial,
    House of Representatives, House of Assembly, Chairmanship, and Councilor.

    Attributes:
        id: UUID primary key
        name: Full name of the election type (e.g., "Presidential Election")
        code: Short code for the election type (e.g., "presidential")
        created_at: Timestamp when record was created
        election_results: Relationship to ElectionResult records
    """

    __tablename__ = "election_types"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
    )

    # Relationships
    election_results: Mapped[list[ElectionResult]] = relationship(
        "ElectionResult",
        back_populates="election_type",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ElectionType(id={self.id}, name='{self.name}', code='{self.code}')>"


class PoliticalParty(BaseModel):
    """Model representing a political party.

    Stores information about Nigerian political parties participating in elections.

    Attributes:
        id: UUID primary key
        name: Full name of the party (e.g., "All Progressives Congress")
        code: Short code/abbreviation (e.g., "APC")
        logo_url: Optional URL to party logo image
        created_at: Timestamp when record was created
        party_results: Relationship to PartyResult records
    """

    __tablename__ = "political_parties"

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
    )
    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    party_results: Mapped[list[PartyResult]] = relationship(
        "PartyResult",
        back_populates="party",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PoliticalParty(id={self.id}, name='{self.name}', code='{self.code}')>"


class ElectionResult(BaseModel):
    """Model representing election results for a polling unit.

    Stores the extracted election data from a result sheet image for a specific
    polling unit and election type combination.

    Attributes:
        id: UUID primary key
        election_type_id: Foreign key to election type
        polling_unit_id: Foreign key to polling unit
        accredited_voters: Number of accredited voters
        valid_votes: Number of valid votes cast
        rejected_votes: Number of rejected/invalid votes
        confidence_score: OCR/extraction confidence score (0.00-1.00)
        source_image_path: Path to the source result sheet image
        extracted_at: Timestamp when data was extracted
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
        election_type: Relationship to ElectionType
        polling_unit: Relationship to PollingUnit
        party_results: Relationship to PartyResult records
        flagged_results: Relationship to FlaggedResult records
    """

    __tablename__ = "election_results"

    election_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("election_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    polling_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("polling_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    accredited_voters: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    valid_votes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    rejected_votes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("0.00"),
    )
    source_image_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    election_type: Mapped[ElectionType] = relationship(
        "ElectionType",
        back_populates="election_results",
    )
    polling_unit: Mapped[PollingUnit] = relationship(
        "PollingUnit",
        back_populates="election_results",
    )
    party_results: Mapped[list[PartyResult]] = relationship(
        "PartyResult",
        back_populates="election_result",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    flagged_results: Mapped[list[FlaggedResult]] = relationship(
        "FlaggedResult",
        back_populates="election_result",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "election_type_id", "polling_unit_id", name="uq_election_result_type_pu"
        ),
        Index("idx_election_results_type", "election_type_id"),
        Index("idx_election_results_pu", "polling_unit_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ElectionResult(id={self.id}, "
            f"election_type_id={self.election_type_id}, "
            f"polling_unit_id={self.polling_unit_id})>"
        )


class PartyResult(BaseModel):
    """Model representing vote count for a party in an election result.

    Stores the vote count and percentage for a specific political party
    within an election result.

    Attributes:
        id: UUID primary key
        election_result_id: Foreign key to election result
        party_id: Foreign key to political party
        vote_count: Number of votes received by the party
        percentage: Percentage of valid votes (0.00-100.00)
        created_at: Timestamp when record was created
        election_result: Relationship to ElectionResult
        party: Relationship to PoliticalParty
    """

    __tablename__ = "party_results"

    election_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("election_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    party_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("political_parties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vote_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
    )

    # Relationships
    election_result: Mapped[ElectionResult] = relationship(
        "ElectionResult",
        back_populates="party_results",
    )
    party: Mapped[PoliticalParty] = relationship(
        "PoliticalParty",
        back_populates="party_results",
    )

    __table_args__ = (
        UniqueConstraint(
            "election_result_id", "party_id", name="uq_party_result_election_party"
        ),
        Index("idx_party_results_election", "election_result_id"),
        Index("idx_party_results_party", "party_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<PartyResult(id={self.id}, "
            f"election_result_id={self.election_result_id}, "
            f"party_id={self.party_id}, "
            f"vote_count={self.vote_count})>"
        )
