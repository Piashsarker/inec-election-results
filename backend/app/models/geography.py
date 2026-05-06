"""SQLAlchemy models for geographic hierarchy.

This module defines the geographic hierarchy models: State, LGA, Ward, and PollingUnit.
These models represent Nigeria's administrative divisions used in elections.

Requirements: 4.1, 4.6
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.election import ElectionResult


class State(BaseModel):
    """Model representing a Nigerian state.

    Nigeria has 36 states plus the Federal Capital Territory (FCT).
    Each state contains multiple Local Government Areas (LGAs).

    Attributes:
        id: UUID primary key
        name: Full name of the state (e.g., "Lagos")
        code: Short code for the state (e.g., "LA")
        total_lgas: Count of LGAs in this state
        created_at: Timestamp when record was created
        lgas: Relationship to child LGA records
    """

    __tablename__ = "states"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        unique=True,
    )
    total_lgas: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    lgas: Mapped[list[LGA]] = relationship(
        "LGA",
        back_populates="state",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<State(id={self.id}, name='{self.name}', code='{self.code}')>"


class LGA(BaseModel):
    """Model representing a Local Government Area.

    LGAs are administrative subdivisions within a state.
    Each LGA contains multiple electoral wards.

    Attributes:
        id: UUID primary key
        state_id: Foreign key to parent state
        name: Full name of the LGA
        code: Code for the LGA (unique within state)
        total_wards: Count of wards in this LGA
        created_at: Timestamp when record was created
        state: Relationship to parent State
        wards: Relationship to child Ward records
    """

    __tablename__ = "lgas"

    state_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("states.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    total_wards: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    state: Mapped[State] = relationship(
        "State",
        back_populates="lgas",
    )
    wards: Mapped[list[Ward]] = relationship(
        "Ward",
        back_populates="lga",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("state_id", "code", name="uq_lga_state_code"),
        Index("idx_lgas_state", "state_id"),
    )

    def __repr__(self) -> str:
        return f"<LGA(id={self.id}, name='{self.name}', code='{self.code}')>"


class Ward(BaseModel):
    """Model representing an electoral ward (Registration Area).

    Wards are subdivisions within an LGA and contain multiple polling units.

    Attributes:
        id: UUID primary key
        lga_id: Foreign key to parent LGA
        name: Full name of the ward
        code: Code for the ward (unique within LGA)
        total_polling_units: Count of polling units in this ward
        created_at: Timestamp when record was created
        lga: Relationship to parent LGA
        polling_units: Relationship to child PollingUnit records
    """

    __tablename__ = "wards"

    lga_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lgas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    total_polling_units: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    lga: Mapped[LGA] = relationship(
        "LGA",
        back_populates="wards",
    )
    polling_units: Mapped[list[PollingUnit]] = relationship(
        "PollingUnit",
        back_populates="ward",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("lga_id", "code", name="uq_ward_lga_code"),
        Index("idx_wards_lga", "lga_id"),
    )

    def __repr__(self) -> str:
        return f"<Ward(id={self.id}, name='{self.name}', code='{self.code}')>"


class PollingUnit(BaseModel):
    """Model representing a polling unit.

    Polling units are the smallest electoral units where votes are cast and counted.
    Each polling unit belongs to a ward and has election results associated with it.

    Attributes:
        id: UUID primary key
        ward_id: Foreign key to parent ward
        name: Full name of the polling unit
        code: Code for the polling unit (unique within ward)
        delimitation: Optional delimitation information
        created_at: Timestamp when record was created
        ward: Relationship to parent Ward
    """

    __tablename__ = "polling_units"

    ward_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    delimitation: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Relationships
    ward: Mapped[Ward] = relationship(
        "Ward",
        back_populates="polling_units",
    )
    election_results: Mapped[list[ElectionResult]] = relationship(
        "ElectionResult",
        back_populates="polling_unit",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("ward_id", "code", name="uq_polling_unit_ward_code"),
        Index("idx_polling_units_ward", "ward_id"),
    )

    def __repr__(self) -> str:
        return f"<PollingUnit(id={self.id}, name='{self.name}', code='{self.code}')>"
