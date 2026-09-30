"""Scraped results API endpoints.

Serves OCR-extracted election results from local JSON files.
This provides immediate access to scraped data without requiring
database seeding. Results are loaded from data/result_sheets/.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Base path for scraped results
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "result_sheets"


class PartyResultItem(BaseModel):
    """Party vote result."""
    code: str
    name: str
    votes: int


class PollingUnitResult(BaseModel):
    """Scraped result for a single polling unit."""
    polling_unit_code: str
    polling_unit_name: str
    file: str
    ocr_confidence: float = 0.0
    extraction_confidence: float = 0.0
    accredited_voters: int = 0
    valid_votes: int = 0
    rejected_votes: int = 0
    parties: list[PartyResultItem] = []
    warnings: list[str] = []
    error: str | None = None


class WardResultSummary(BaseModel):
    """Aggregated ward-level results."""
    election: str
    date: str
    state: str
    lga: str
    ward: str
    ward_code: str
    polling_units_processed: int
    polling_units_total: int
    total_accredited_voters: int
    total_valid_votes: int
    total_rejected_votes: int
    party_totals: dict[str, int]
    results: list[PollingUnitResult]


class ScrapedElectionSummary(BaseModel):
    """Summary of a scraped election data folder."""
    folder: str
    election: str
    date: str
    state: str
    lga: str
    ward: str
    polling_units_total: int
    polling_units_processed: int


@router.get("", response_model=list[ScrapedElectionSummary])
async def list_scraped_results() -> list[ScrapedElectionSummary]:
    """List all available scraped election results.

    Returns:
        List of scraped election summaries
    """
    summaries: list[ScrapedElectionSummary] = []

    if not DATA_DIR.exists():
        return summaries

    for folder in sorted(DATA_DIR.iterdir()):
        if not folder.is_dir():
            continue

        # Look for results JSON files
        for json_file in folder.glob("results*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)

                summaries.append(ScrapedElectionSummary(
                    folder=folder.name,
                    election=data.get("election", "Unknown"),
                    date=data.get("date", "Unknown"),
                    state=data.get("state", "Unknown"),
                    lga=data.get("lga", "Unknown"),
                    ward=data.get("ward", "Unknown"),
                    polling_units_total=data.get("polling_units_total", 0),
                    polling_units_processed=data.get("polling_units_processed", 0),
                ))
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to read {json_file}: {e}")

    return summaries


@router.get("/{folder}", response_model=WardResultSummary)
async def get_scraped_ward_results(folder: str) -> WardResultSummary:
    """Get detailed results for a scraped ward.

    Args:
        folder: Name of the results folder (e.g., 'osun_governorship_2026')

    Returns:
        Full ward results with per-polling-unit breakdown
    """
    # Prevent path traversal attacks
    if ".." in folder or "/" in folder or "\\" in folder:
        raise HTTPException(status_code=400, detail="Invalid folder name")

    folder_path = DATA_DIR / folder

    if not folder_path.exists() or not folder_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Results folder '{folder}' not found")

    # Try tesseract results first, then regular results
    json_file = folder_path / "results_tesseract.json"
    if not json_file.exists():
        json_file = folder_path / "results.json"
    if not json_file.exists():
        raise HTTPException(status_code=404, detail="No results file found in folder")

    try:
        with open(json_file) as f:
            data: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse results: {e}")

    # Parse individual results
    results: list[PollingUnitResult] = []
    for r in data.get("results", []):
        parties = [
            PartyResultItem(
                code=p.get("code", ""),
                name=p.get("name", ""),
                votes=p.get("votes", 0),
            )
            for p in r.get("parties", [])
        ]

        results.append(PollingUnitResult(
            polling_unit_code=r.get("polling_unit_code", ""),
            polling_unit_name=r.get("polling_unit_name", ""),
            file=r.get("file", ""),
            ocr_confidence=r.get("ocr_confidence", 0.0),
            extraction_confidence=r.get("extraction_confidence", 0.0),
            accredited_voters=r.get("accredited_voters", 0),
            valid_votes=r.get("valid_votes", 0),
            rejected_votes=r.get("rejected_votes", 0),
            parties=parties,
            warnings=r.get("warnings", []),
            error=r.get("error"),
        ))

    return WardResultSummary(
        election=data.get("election", "Unknown"),
        date=data.get("date", "Unknown"),
        state=data.get("state", "Unknown"),
        lga=data.get("lga", "Unknown"),
        ward=data.get("ward", "Unknown"),
        ward_code=data.get("ward_code", "Unknown"),
        polling_units_processed=data.get("polling_units_processed", 0),
        polling_units_total=data.get("polling_units_total", 0),
        total_accredited_voters=data.get("total_accredited_voters", 0),
        total_valid_votes=data.get("total_valid_votes", 0),
        total_rejected_votes=data.get("total_rejected_votes", 0),
        party_totals=data.get("party_totals", {}),
        results=results,
    )
