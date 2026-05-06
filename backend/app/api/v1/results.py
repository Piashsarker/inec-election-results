"""Results API endpoints.

Provides endpoints for viewing and managing election results.

Requirements: 4.6, 3.6
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_async_session
from app.models import ElectionResult, FlaggedResult

router = APIRouter()


class PartyResultResponse(BaseModel):
    """Party result response schema."""
    id: UUID
    party_id: UUID
    vote_count: int
    percentage: float

    class Config:
        from_attributes = True


class ElectionResultResponse(BaseModel):
    """Election result response schema."""
    id: UUID
    election_type_id: UUID
    polling_unit_id: UUID
    accredited_voters: int
    valid_votes: int
    rejected_votes: int
    confidence_score: float
    source_image_path: str | None
    party_results: list[PartyResultResponse] = []

    class Config:
        from_attributes = True


class FlagResultRequest(BaseModel):
    """Request to flag a result for review."""
    reason: str


class FlaggedResultResponse(BaseModel):
    """Flagged result response schema."""
    id: UUID
    election_result_id: UUID
    reason: str
    status: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[ElectionResultResponse])
async def get_results(
    election_type_id: UUID | None = Query(None),
    polling_unit_id: UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
) -> list[ElectionResultResponse]:
    """Get election results with optional filtering.

    Args:
        election_type_id: Filter by election type
        polling_unit_id: Filter by polling unit
        limit: Maximum results to return
        offset: Number of results to skip

    Returns:
        List of election results
    """
    query = select(ElectionResult).options(selectinload(ElectionResult.party_results))

    if election_type_id:
        query = query.where(ElectionResult.election_type_id == election_type_id)
    if polling_unit_id:
        query = query.where(ElectionResult.polling_unit_id == polling_unit_id)

    query = query.limit(limit).offset(offset)

    result = await session.execute(query)
    results = result.scalars().all()

    return [ElectionResultResponse.model_validate(r) for r in results]


@router.get("/{result_id}", response_model=ElectionResultResponse)
async def get_result(
    result_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> ElectionResultResponse:
    """Get a single election result by ID.

    Args:
        result_id: Election result UUID

    Returns:
        Election result with party results
    """
    result = await session.execute(
        select(ElectionResult)
        .options(selectinload(ElectionResult.party_results))
        .where(ElectionResult.id == result_id)
    )
    election_result = result.scalar_one_or_none()

    if not election_result:
        raise HTTPException(status_code=404, detail="Result not found")

    return ElectionResultResponse.model_validate(election_result)


@router.post("/flag/{result_id}", response_model=FlaggedResultResponse)
async def flag_result(
    result_id: UUID,
    request: FlagResultRequest,
    session: AsyncSession = Depends(get_async_session),
) -> FlaggedResultResponse:
    """Flag a result for manual review.

    Args:
        result_id: Election result UUID
        request: Flag reason

    Returns:
        Created flagged result record
    """
    # Verify result exists
    result = await session.execute(
        select(ElectionResult).where(ElectionResult.id == result_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Result not found")

    # Create flagged result
    flagged = FlaggedResult(
        election_result_id=result_id,
        reason=request.reason,
        status="pending",
    )
    session.add(flagged)
    await session.commit()
    await session.refresh(flagged)

    return FlaggedResultResponse.model_validate(flagged)
