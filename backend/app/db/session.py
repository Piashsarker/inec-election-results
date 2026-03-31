"""Database session management for INEC Election Results Agent.

This module provides database session configuration and dependency injection
for FastAPI endpoints.

Requirements: 4.1, 4.6
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.database.async_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session.
    
    Yields:
        AsyncSession: An async SQLAlchemy session
        
    Example:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_async_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Type alias for dependency injection
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
