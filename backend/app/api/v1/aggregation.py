"""Aggregation API endpoints.

Provides endpoints for viewing aggregated election results at ward, LGA, and state levels.

Requirements: 5.1, 5.2
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.aggregator.service import AggregationService
from app.db.session import get_async_session

router = APIRouter()


class PartyAggregationResponse(BaseModel):
    """Party aggregation response schema."""
    party_id: UUID
    party_name: str
    party_code: str
    total_votes: int
    percentage: float
    rank: int

    class Config:
        from_attributes = True


class AggregationResponse(BaseModel):
    """Aggregation response schema."""
    level: str
    location_id: UUID
    location_name: str
    election_type_id: UUID
    election_type_code: str
    party_results: list[PartyAggregationResponse] = []
    total_valid_votes: int = 0
    total_accredited_voters: int = 0
    total_rejected_votes: int = 0
    total_polling_units: int = 0
    processed_polling_units: int = 0
    flagged_polling_units: int = 0

    class Config:
        from_attributes = True


def _convert_aggregation_result(agg_result) -> AggregationResponse:
    """Convert AggregationResult dataclass to Pydantic response model."""
    return AggregationResponse(
        level=agg_result.level,
        location_id=agg_result.location_id,
        location_name=agg_result.location_name,
        election_type_id=agg_result.election_type_id,
        election_type_code=agg_result.election_type_code,
        party_results=[
            PartyAggregationResponse(
                party_id=pr.party_id,
                party_name=pr.party_name,
                party_code=pr.party_code,
                total_votes=pr.total_votes,
                percentage=float(pr.percentage),
                rank=pr.rank,
            )
            for pr in agg_result.party_results
        ],
        total_valid_votes=agg_result.total_valid_votes,
        total_accredited_voters=agg_result.total_accredited_voters,
        total_rejected_votes=agg_result.total_rejected_votes,
        total_polling_units=agg_result.total_polling_units,
        processed_polling_units=agg_result.processed_polling_units,
        flagged_polling_units=agg_result.flagged_polling_units,
    )


@router.get("/ward/{ward_id}", response_model=AggregationResponse)
async def get_ward_aggregation(
    ward_id: UUID,
    election_type_id: UUID = Query(..., description="Election type UUID"),
    session: AsyncSession = Depends(get_async_session),
) -> AggregationResponse:
    """Get aggregated election results for a ward.
    
    Sums vote counts by party across all polling units in the specified ward.
    
    Args:
        ward_id: Ward UUID
        election_type_id: Election type UUID
        
    Returns:
        Aggregated results with party rankings and polling unit counts
        
    Requirements: 5.1, 5.3, 5.4, 5.5, 5.6
    """
    service = AggregationService(session)
    result = await service.aggregate_ward(ward_id, election_type_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Ward or election type not found"
        )

    return _convert_aggregation_result(result)


@router.get("/lga/{lga_id}", response_model=AggregationResponse)
async def get_lga_aggregation(
    lga_id: UUID,
    election_type_id: UUID = Query(..., description="Election type UUID"),
    session: AsyncSession = Depends(get_async_session),
) -> AggregationResponse:
    """Get aggregated election results for an LGA.
    
    Sums vote counts by party across all wards (and their polling units) in the LGA.
    
    Args:
        lga_id: LGA UUID
        election_type_id: Election type UUID
        
    Returns:
        Aggregated results with party rankings and polling unit counts
        
    Requirements: 5.2, 5.3, 5.4, 5.5, 5.6
    """
    service = AggregationService(session)
    result = await service.aggregate_lga(lga_id, election_type_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="LGA or election type not found"
        )

    return _convert_aggregation_result(result)


@router.get("/state/{state_id}", response_model=AggregationResponse)
async def get_state_aggregation(
    state_id: UUID,
    election_type_id: UUID = Query(..., description="Election type UUID"),
    session: AsyncSession = Depends(get_async_session),
) -> AggregationResponse:
    """Get aggregated election results for a state.
    
    Sums vote counts by party across all LGAs (and their wards/polling units) in the state.
    
    Args:
        state_id: State UUID
        election_type_id: Election type UUID
        
    Returns:
        Aggregated results with party rankings and polling unit counts
        
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
    """
    service = AggregationService(session)
    result = await service.aggregate_state(state_id, election_type_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="State or election type not found"
        )

    return _convert_aggregation_result(result)
