"""API v1 endpoints."""

from fastapi import APIRouter

from app.api.v1 import aggregation, elections, export, jobs, results, scraped_results

router = APIRouter()

router.include_router(elections.router, prefix="/elections", tags=["elections"])
router.include_router(results.router, prefix="/results", tags=["results"])
router.include_router(aggregation.router, prefix="/aggregation", tags=["aggregation"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(export.router, prefix="/export", tags=["export"])
router.include_router(scraped_results.router, prefix="/scraped", tags=["scraped"])
