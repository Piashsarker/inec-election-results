"""Export API endpoints.

Provides endpoints for exporting election results in CSV and JSON formats.

Requirements: 8.1, 8.2, 8.3, 8.4
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_async_session
from app.workers.tasks import generate_csv_export, generate_json_export

router = APIRouter()
settings = get_settings()


class ExportRequest(BaseModel):
    """Request schema for export generation."""
    election_type_id: str | None = None
    state_id: str | None = None
    lga_id: str | None = None
    ward_id: str | None = None
    include_metadata: bool = True


class JSONExportRequest(ExportRequest):
    """Request schema for JSON export generation."""
    aggregation_level: str | None = None  # 'ward', 'lga', 'state', or None for detailed


class ExportResponse(BaseModel):
    """Response schema for export generation."""
    export_id: str
    format: str
    status: str
    message: str
    filters: dict


class ExportStatusResponse(BaseModel):
    """Response schema for export status check."""
    export_id: str
    format: str
    status: str
    file_path: str | None = None
    record_count: int | None = None
    generated_at: str | None = None
    filters: dict | None = None
    error: str | None = None


@router.post("/csv", response_model=ExportResponse)
async def create_csv_export(
    request: ExportRequest,
    session: AsyncSession = Depends(get_async_session),
) -> ExportResponse:
    """Start a CSV export generation task.

    Queues a background task to generate a CSV file with election results
    based on the provided filters.

    Args:
        request: Export configuration with optional filters

    Returns:
        Export ID for tracking and download

    Requirements: 8.1, 8.3
    """
    export_id = str(uuid.uuid4())

    # Queue the Celery task
    task = generate_csv_export.delay(
        export_id=export_id,
        election_type_id=request.election_type_id,
        state_id=request.state_id,
        lga_id=request.lga_id,
        ward_id=request.ward_id,
        include_metadata=request.include_metadata,
    )

    return ExportResponse(
        export_id=export_id,
        format="csv",
        status="queued",
        message=f"CSV export queued with task ID: {task.id}",
        filters={
            "election_type_id": request.election_type_id,
            "state_id": request.state_id,
            "lga_id": request.lga_id,
            "ward_id": request.ward_id,
        },
    )


@router.post("/json", response_model=ExportResponse)
async def create_json_export(
    request: JSONExportRequest,
    session: AsyncSession = Depends(get_async_session),
) -> ExportResponse:
    """Start a JSON export generation task.

    Queues a background task to generate a JSON file with election results
    based on the provided filters. Optionally aggregates results at ward,
    LGA, or state level.

    Args:
        request: Export configuration with optional filters and aggregation level

    Returns:
        Export ID for tracking and download

    Requirements: 8.2, 8.3, 8.4
    """
    export_id = str(uuid.uuid4())

    # Validate aggregation level if provided
    if request.aggregation_level and request.aggregation_level not in ("ward", "lga", "state"):
        raise HTTPException(
            status_code=400,
            detail="Invalid aggregation_level. Must be 'ward', 'lga', 'state', or null"
        )

    # Queue the Celery task
    task = generate_json_export.delay(
        export_id=export_id,
        election_type_id=request.election_type_id,
        state_id=request.state_id,
        lga_id=request.lga_id,
        ward_id=request.ward_id,
        include_metadata=request.include_metadata,
        aggregation_level=request.aggregation_level,
    )

    return ExportResponse(
        export_id=export_id,
        format="json",
        status="queued",
        message=f"JSON export queued with task ID: {task.id}",
        filters={
            "election_type_id": request.election_type_id,
            "state_id": request.state_id,
            "lga_id": request.lga_id,
            "ward_id": request.ward_id,
            "aggregation_level": request.aggregation_level,
        },
    )


@router.get("/{export_id}/status", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: str,
) -> ExportStatusResponse:
    """Check the status of an export generation task.

    Args:
        export_id: Export UUID

    Returns:
        Export status and file information if complete

    Requirements: 8.1, 8.2
    """
    export_dir = os.path.join(settings.scraping.storage_path, "exports")

    # Check for CSV file
    csv_path = os.path.join(export_dir, f"{export_id}.csv")
    if os.path.exists(csv_path):
        stat = os.stat(csv_path)
        return ExportStatusResponse(
            export_id=export_id,
            format="csv",
            status="completed",
            file_path=csv_path,
            generated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        )

    # Check for JSON file
    json_path = os.path.join(export_dir, f"{export_id}.json")
    if os.path.exists(json_path):
        stat = os.stat(json_path)
        return ExportStatusResponse(
            export_id=export_id,
            format="json",
            status="completed",
            file_path=json_path,
            generated_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        )

    # File not found - could be still processing or failed
    return ExportStatusResponse(
        export_id=export_id,
        format="unknown",
        status="pending",
    )


@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    format: str | None = Query(None, description="File format (csv or json)"),
) -> FileResponse:
    """Download a generated export file.

    Args:
        export_id: Export UUID
        format: Optional format hint (csv or json)

    Returns:
        File download response

    Requirements: 8.1, 8.2, 8.4
    """
    export_dir = os.path.join(settings.scraping.storage_path, "exports")

    # Determine file path based on format hint or check both
    if format == "csv":
        file_path = os.path.join(export_dir, f"{export_id}.csv")
        media_type = "text/csv"
        filename = f"election_results_{export_id}.csv"
    elif format == "json":
        file_path = os.path.join(export_dir, f"{export_id}.json")
        media_type = "application/json"
        filename = f"election_results_{export_id}.json"
    else:
        # Try CSV first, then JSON
        csv_path = os.path.join(export_dir, f"{export_id}.csv")
        json_path = os.path.join(export_dir, f"{export_id}.json")

        if os.path.exists(csv_path):
            file_path = csv_path
            media_type = "text/csv"
            filename = f"election_results_{export_id}.csv"
        elif os.path.exists(json_path):
            file_path = json_path
            media_type = "application/json"
            filename = f"election_results_{export_id}.json"
        else:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Export file not found. It may still be processing"
                    " or the export ID is invalid."
                ),
            )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Export file not found. It may still be processing or the export ID is invalid."
        )

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
