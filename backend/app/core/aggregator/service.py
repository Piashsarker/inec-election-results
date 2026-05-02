"""Aggregation service for election results.

This module provides the AggregationService class that aggregates election results
at ward, LGA, and state levels, calculates vote percentages, and ranks parties.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.election import ElectionResult, ElectionType, PartyResult, PoliticalParty
from app.models.geography import LGA, PollingUnit, State, Ward
from app.models.job import FlaggedResult


@dataclass
class PartyAggregation:
    """Aggregated vote data for a single party.

    Attributes:
        party_id: UUID of the political party
        party_name: Full name of the party
        party_code: Short code/abbreviation of the party
        total_votes: Sum of votes across all polling units
        percentage: Percentage of total valid votes
        rank: Party ranking by vote count (1 = highest)
    """
    party_id: uuid.UUID
    party_name: str
    party_code: str
    total_votes: int
    percentage: Decimal = Decimal("0.00")
    rank: int = 0


@dataclass
class AggregationResult:
    """Result of vote aggregation at a geographic level.

    Attributes:
        level: Geographic level ('ward', 'lga', 'state')
        location_id: UUID of the geographic location
        location_name: Name of the geographic location
        election_type_id: UUID of the election type
        election_type_code: Code of the election type
        party_results: List of aggregated party results
        total_valid_votes: Sum of valid votes across all polling units
        total_accredited_voters: Sum of accredited voters
        total_rejected_votes: Sum of rejected votes
        total_polling_units: Total number of polling units in the area
        processed_polling_units: Number of polling units with results
        flagged_polling_units: Number of polling units with flagged results
    """
    level: str
    location_id: uuid.UUID
    location_name: str
    election_type_id: uuid.UUID
    election_type_code: str
    party_results: list[PartyAggregation] = field(default_factory=list)
    total_valid_votes: int = 0
    total_accredited_voters: int = 0
    total_rejected_votes: int = 0
    total_polling_units: int = 0
    processed_polling_units: int = 0
    flagged_polling_units: int = 0


class AggregationService:
    """Service for aggregating election results at different geographic levels.

    This service queries election results from the database, groups them by
    geographic level (ward, LGA, state), sums party votes, calculates percentages,
    ranks parties by vote count, and tracks polling unit counts and flagged results.

    Requirements:
        - 5.1: Ward-level aggregation (sum votes from polling units in a ward)
        - 5.2: LGA-level aggregation (sum votes from wards in an LGA)
        - 5.3: Calculate percentages for each party
        - 5.4: Rank parties by vote count in descending order
        - 5.5: Report total polling units included in aggregation
        - 5.6: Report polling units with missing or flagged results
    """

    def __init__(self, session: AsyncSession):
        """Initialize the aggregation service.

        Args:
            session: Async SQLAlchemy database session
        """
        self.session = session

    async def aggregate_ward(
        self,
        ward_id: uuid.UUID,
        election_type_id: uuid.UUID,
    ) -> AggregationResult | None:
        """Aggregate election results at ward level.

        Sums vote counts by party across all polling units in the specified ward.

        Args:
            ward_id: UUID of the ward to aggregate
            election_type_id: UUID of the election type

        Returns:
            AggregationResult with ward-level aggregation, or None if ward not found

        Requirements: 5.1, 5.3, 5.4, 5.5, 5.6
        """
        # Get ward details
        ward_query = select(Ward).where(Ward.id == ward_id)
        ward_result = await self.session.execute(ward_query)
        ward = ward_result.scalar_one_or_none()

        if ward is None:
            return None

        # Get election type details
        election_type_query = select(ElectionType).where(ElectionType.id == election_type_id)
        election_type_result = await self.session.execute(election_type_query)
        election_type = election_type_result.scalar_one_or_none()

        if election_type is None:
            return None

        # Get polling unit IDs in this ward
        pu_query = select(PollingUnit.id).where(PollingUnit.ward_id == ward_id)
        pu_result = await self.session.execute(pu_query)
        polling_unit_ids = [row[0] for row in pu_result.fetchall()]

        return await self._aggregate_for_polling_units(
            level="ward",
            location_id=ward_id,
            location_name=ward.name,
            election_type_id=election_type_id,
            election_type_code=election_type.code,
            polling_unit_ids=polling_unit_ids,
            total_polling_units=ward.total_polling_units,
        )

    async def aggregate_lga(
        self,
        lga_id: uuid.UUID,
        election_type_id: uuid.UUID,
    ) -> AggregationResult | None:
        """Aggregate election results at LGA level.

        Sums vote counts by party across all wards (and their polling units) in the LGA.

        Args:
            lga_id: UUID of the LGA to aggregate
            election_type_id: UUID of the election type

        Returns:
            AggregationResult with LGA-level aggregation, or None if LGA not found

        Requirements: 5.2, 5.3, 5.4, 5.5, 5.6
        """
        # Get LGA details
        lga_query = select(LGA).where(LGA.id == lga_id)
        lga_result = await self.session.execute(lga_query)
        lga = lga_result.scalar_one_or_none()

        if lga is None:
            return None

        # Get election type details
        election_type_query = select(ElectionType).where(ElectionType.id == election_type_id)
        election_type_result = await self.session.execute(election_type_query)
        election_type = election_type_result.scalar_one_or_none()

        if election_type is None:
            return None

        # Get all polling unit IDs in this LGA (through wards)
        pu_query = (
            select(PollingUnit.id)
            .join(Ward, PollingUnit.ward_id == Ward.id)
            .where(Ward.lga_id == lga_id)
        )
        pu_result = await self.session.execute(pu_query)
        polling_unit_ids = [row[0] for row in pu_result.fetchall()]

        # Calculate total polling units in LGA
        total_pu_query = (
            select(func.sum(Ward.total_polling_units))
            .where(Ward.lga_id == lga_id)
        )
        total_pu_result = await self.session.execute(total_pu_query)
        total_polling_units = total_pu_result.scalar() or 0

        return await self._aggregate_for_polling_units(
            level="lga",
            location_id=lga_id,
            location_name=lga.name,
            election_type_id=election_type_id,
            election_type_code=election_type.code,
            polling_unit_ids=polling_unit_ids,
            total_polling_units=total_polling_units,
        )

    async def aggregate_state(
        self,
        state_id: uuid.UUID,
        election_type_id: uuid.UUID,
    ) -> AggregationResult | None:
        """Aggregate election results at state level.

        Sums vote counts by party across all LGAs (and their wards/polling units) in the state.

        Args:
            state_id: UUID of the state to aggregate
            election_type_id: UUID of the election type

        Returns:
            AggregationResult with state-level aggregation, or None if state not found

        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
        """
        # Get state details
        state_query = select(State).where(State.id == state_id)
        state_result = await self.session.execute(state_query)
        state = state_result.scalar_one_or_none()

        if state is None:
            return None

        # Get election type details
        election_type_query = select(ElectionType).where(ElectionType.id == election_type_id)
        election_type_result = await self.session.execute(election_type_query)
        election_type = election_type_result.scalar_one_or_none()

        if election_type is None:
            return None

        # Get all polling unit IDs in this state (through LGAs and wards)
        pu_query = (
            select(PollingUnit.id)
            .join(Ward, PollingUnit.ward_id == Ward.id)
            .join(LGA, Ward.lga_id == LGA.id)
            .where(LGA.state_id == state_id)
        )
        pu_result = await self.session.execute(pu_query)
        polling_unit_ids = [row[0] for row in pu_result.fetchall()]

        # Calculate total polling units in state
        total_pu_query = (
            select(func.sum(Ward.total_polling_units))
            .join(LGA, Ward.lga_id == LGA.id)
            .where(LGA.state_id == state_id)
        )
        total_pu_result = await self.session.execute(total_pu_query)
        total_polling_units = total_pu_result.scalar() or 0

        return await self._aggregate_for_polling_units(
            level="state",
            location_id=state_id,
            location_name=state.name,
            election_type_id=election_type_id,
            election_type_code=election_type.code,
            polling_unit_ids=polling_unit_ids,
            total_polling_units=total_polling_units,
        )

    async def _aggregate_for_polling_units(
        self,
        level: str,
        location_id: uuid.UUID,
        location_name: str,
        election_type_id: uuid.UUID,
        election_type_code: str,
        polling_unit_ids: list[uuid.UUID],
        total_polling_units: int,
    ) -> AggregationResult:
        """Aggregate results for a list of polling units.

        This is the core aggregation logic used by ward, LGA, and state aggregation.

        Args:
            level: Geographic level ('ward', 'lga', 'state')
            location_id: UUID of the geographic location
            location_name: Name of the geographic location
            election_type_id: UUID of the election type
            election_type_code: Code of the election type
            polling_unit_ids: List of polling unit UUIDs to aggregate
            total_polling_units: Total number of polling units in the area

        Returns:
            AggregationResult with aggregated data
        """
        if not polling_unit_ids:
            return AggregationResult(
                level=level,
                location_id=location_id,
                location_name=location_name,
                election_type_id=election_type_id,
                election_type_code=election_type_code,
                total_polling_units=total_polling_units,
            )

        # Get election results for these polling units
        results_query = (
            select(ElectionResult)
            .where(
                ElectionResult.polling_unit_id.in_(polling_unit_ids),
                ElectionResult.election_type_id == election_type_id,
            )
        )
        results_result = await self.session.execute(results_query)
        election_results = results_result.scalars().all()

        # Calculate totals from election results
        total_valid_votes = sum(er.valid_votes for er in election_results)
        total_accredited_voters = sum(er.accredited_voters for er in election_results)
        total_rejected_votes = sum(er.rejected_votes for er in election_results)
        processed_polling_units = len(election_results)

        # Get election result IDs for party result aggregation
        election_result_ids = [er.id for er in election_results]

        # Aggregate party votes
        party_aggregations = await self._aggregate_party_votes(
            election_result_ids=election_result_ids,
            total_valid_votes=total_valid_votes,
        )

        # Count flagged results
        flagged_count = await self._count_flagged_results(election_result_ids)

        return AggregationResult(
            level=level,
            location_id=location_id,
            location_name=location_name,
            election_type_id=election_type_id,
            election_type_code=election_type_code,
            party_results=party_aggregations,
            total_valid_votes=total_valid_votes,
            total_accredited_voters=total_accredited_voters,
            total_rejected_votes=total_rejected_votes,
            total_polling_units=total_polling_units,
            processed_polling_units=processed_polling_units,
            flagged_polling_units=flagged_count,
        )

    async def _aggregate_party_votes(
        self,
        election_result_ids: list[uuid.UUID],
        total_valid_votes: int,
    ) -> list[PartyAggregation]:
        """Aggregate votes by party and calculate percentages and rankings.

        Args:
            election_result_ids: List of election result UUIDs to aggregate
            total_valid_votes: Total valid votes for percentage calculation

        Returns:
            List of PartyAggregation sorted by vote count (descending)

        Requirements: 5.3, 5.4
        """
        if not election_result_ids:
            return []

        # Query to sum votes by party
        party_votes_query = (
            select(
                PoliticalParty.id,
                PoliticalParty.name,
                PoliticalParty.code,
                func.sum(PartyResult.vote_count).label("total_votes"),
            )
            .join(PartyResult, PoliticalParty.id == PartyResult.party_id)
            .where(PartyResult.election_result_id.in_(election_result_ids))
            .group_by(PoliticalParty.id, PoliticalParty.name, PoliticalParty.code)
            .order_by(func.sum(PartyResult.vote_count).desc())
        )

        party_votes_result = await self.session.execute(party_votes_query)
        party_rows = party_votes_result.fetchall()

        # Build party aggregations with percentages and rankings
        party_aggregations: list[PartyAggregation] = []

        for rank, row in enumerate(party_rows, start=1):
            party_id, party_name, party_code, votes = row

            # Calculate percentage (avoid division by zero)
            percentage = Decimal("0.00")
            if total_valid_votes > 0:
                percentage = Decimal(str(votes * 100 / total_valid_votes)).quantize(
                    Decimal("0.01")
                )

            party_aggregations.append(
                PartyAggregation(
                    party_id=party_id,
                    party_name=party_name,
                    party_code=party_code,
                    total_votes=votes,
                    percentage=percentage,
                    rank=rank,
                )
            )

        return party_aggregations

    async def _count_flagged_results(
        self,
        election_result_ids: list[uuid.UUID],
    ) -> int:
        """Count the number of flagged results.

        Args:
            election_result_ids: List of election result UUIDs to check

        Returns:
            Number of flagged results

        Requirements: 5.6
        """
        if not election_result_ids:
            return 0

        flagged_query = (
            select(func.count(FlaggedResult.id))
            .where(FlaggedResult.election_result_id.in_(election_result_ids))
        )
        flagged_result = await self.session.execute(flagged_query)
        return flagged_result.scalar() or 0

    @staticmethod
    def calculate_percentage(votes: int, total_votes: int) -> Decimal:
        """Calculate vote percentage.

        Args:
            votes: Number of votes for a party
            total_votes: Total valid votes

        Returns:
            Percentage as Decimal with 2 decimal places

        Requirements: 5.3
        """
        if total_votes <= 0:
            return Decimal("0.00")
        return Decimal(str(votes * 100 / total_votes)).quantize(Decimal("0.01"))

    @staticmethod
    def rank_parties(party_results: list[PartyAggregation]) -> list[PartyAggregation]:
        """Rank parties by vote count in descending order.

        Args:
            party_results: List of party aggregations to rank

        Returns:
            List of party aggregations with rank field updated

        Requirements: 5.4
        """
        # Sort by total_votes descending
        sorted_results = sorted(
            party_results,
            key=lambda p: p.total_votes,
            reverse=True,
        )

        # Assign ranks
        for rank, party in enumerate(sorted_results, start=1):
            party.rank = rank

        return sorted_results
