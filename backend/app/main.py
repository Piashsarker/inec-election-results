"""FastAPI application entry point for INEC Election Results Agent.

This module initializes the FastAPI application with all routes,
middleware, and configuration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI Agent for extracting Nigerian election results from INEC IREV portal",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict:
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
        }
    
    # Include API routers
    from app.api.v1 import router as api_router
    app.include_router(api_router, prefix=settings.api_prefix)
    
    return app


# Create application instance
app = create_app()
