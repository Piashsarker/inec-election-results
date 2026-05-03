"""Elections API endpoints.

Provides endpoints for navigating the election hierarchy:
- Election types
- States
- LGAs
- Wards
- Polling units

Requirements: 1.2, 1.3, 1.4, 1.5, 1.6
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models import LGA, ElectionType, PollingUnit, State, Ward

router = APIRouter()


# Response schemas
class ElectionTypeResponse(BaseModel):
    """Election type response schema."""
    id: UUID
    name: str
    code: str

    class Config:
        from_attributes = True


class StateResponse(BaseModel):
    """State response schema."""
    id: UUID
    name: str
    code: str
    total_lgas: int

    class Config:
        from_attributes = True


class LGAResponse(BaseModel):
    """LGA response schema."""
    id: UUID
    state_id: UUID
    name: str
    code: str
    total_wards: int

    class Config:
        from_attributes = True


class WardResponse(BaseModel):
    """Ward response schema."""
    id: UUID
    lga_id: UUID
    name: str
    code: str
    total_polling_units: int

    class Config:
        from_attributes = True


class PollingUnitResponse(BaseModel):
    """Polling unit response schema."""
    id: UUID
    ward_id: UUID
    name: str
    code: str
    delimitation: str | None

    class Config:
        from_attributes = True


@router.get("/types", response_model=list[ElectionTypeResponse])
async def get_election_types(
    session: AsyncSession = Depends(get_async_session),
) -> list[ElectionTypeResponse]:
    """Get all available election types.

    Returns:
        List of election types (Presidential, Governorship, etc.)
    """
    result = await session.execute(select(ElectionType).order_by(ElectionType.name))
    election_types = result.scalars().all()
    return [ElectionTypeResponse.model_validate(et) for et in election_types]


@router.get("/{election_type}/states", response_model=list[StateResponse])
async def get_states(
    election_type: str,
    session: AsyncSession = Depends(get_async_session),
) -> list[StateResponse]:
    """Get all states for an election type.

    Args:
        election_type: Election type code (e.g., 'presidential')

    Returns:
        List of 37 states (36 states + FCT)
    """
    # Verify election type exists
    et_result = await session.execute(
        select(ElectionType).where(ElectionType.code == election_type)
    )
    if not et_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Election type '{election_type}' not found")

    result = await session.execute(select(State).order_by(State.name))
    states = result.scalars().all()
    return [StateResponse.model_validate(s) for s in states]


@router.get("/{election_type}/{state}/lgas", response_model=list[LGAResponse])
async def get_lgas(
    election_type: str,
    state: str,
    session: AsyncSession = Depends(get_async_session),
) -> list[LGAResponse]:
    """Get all LGAs for a state.

    Args:
        election_type: Election type code
        state: State code

    Returns:
        List of LGAs in the state
    """
    # Get state by code
    state_result = await session.execute(
        select(State).where(State.code == state)
    )
    state_obj = state_result.scalar_one_or_none()
    if not state_obj:
        raise HTTPException(status_code=404, detail=f"State '{state}' not found")

    result = await session.execute(
        select(LGA).where(LGA.state_id == state_obj.id).order_by(LGA.name)
    )
    lgas = result.scalars().all()
    return [LGAResponse.model_validate(lga) for lga in lgas]


@router.get("/{election_type}/{state}/{lga}/wards", response_model=list[WardResponse])
async def get_wards(
    election_type: str,
    state: str,
    lga: str,
    session: AsyncSession = Depends(get_async_session),
) -> list[WardResponse]:
    """Get all wards for an LGA.

    Args:
        election_type: Election type code
        state: State code
        lga: LGA code

    Returns:
        List of wards in the LGA
    """
    # Get state first
    state_result = await session.execute(
        select(State).where(State.code == state)
    )
    state_obj = state_result.scalar_one_or_none()
    if not state_obj:
        raise HTTPException(status_code=404, detail=f"State '{state}' not found")

    # Get LGA
    lga_result = await session.execute(
        select(LGA).where(LGA.state_id == state_obj.id, LGA.code == lga)
    )
    lga_obj = lga_result.scalar_one_or_none()
    if not lga_obj:
        raise HTTPException(status_code=404, detail=f"LGA '{lga}' not found in state '{state}'")

    result = await session.execute(
        select(Ward).where(Ward.lga_id == lga_obj.id).order_by(Ward.name)
    )
    wards = result.scalars().all()
    return [WardResponse.model_validate(w) for w in wards]


@router.get(
    "/{election_type}/{state}/{lga}/{ward}/polling-units",
    response_model=list[PollingUnitResponse],
)
async def get_polling_units(
    election_type: str,
    state: str,
    lga: str,
    ward: str,
    session: AsyncSession = Depends(get_async_session),
) -> list[PollingUnitResponse]:
    """Get all polling units for a ward.

    Args:
        election_type: Election type code
        state: State code
        lga: LGA code
        ward: Ward code

    Returns:
        List of polling units in the ward
    """
    # Get state
    state_result = await session.execute(
        select(State).where(State.code == state)
    )
    state_obj = state_result.scalar_one_or_none()
    if not state_obj:
        raise HTTPException(status_code=404, detail=f"State '{state}' not found")

    # Get LGA
    lga_result = await session.execute(
        select(LGA).where(LGA.state_id == state_obj.id, LGA.code == lga)
    )
    lga_obj = lga_result.scalar_one_or_none()
    if not lga_obj:
        raise HTTPException(status_code=404, detail=f"LGA '{lga}' not found")

    # Get Ward
    ward_result = await session.execute(
        select(Ward).where(Ward.lga_id == lga_obj.id, Ward.code == ward)
    )
    ward_obj = ward_result.scalar_one_or_none()
    if not ward_obj:
        raise HTTPException(status_code=404, detail=f"Ward '{ward}' not found")

    result = await session.execute(
        select(PollingUnit).where(PollingUnit.ward_id == ward_obj.id).order_by(PollingUnit.name)
    )
    polling_units = result.scalars().all()
    return [PollingUnitResponse.model_validate(pu) for pu in polling_units]
