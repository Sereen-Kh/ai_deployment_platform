"""Shared database utilities for microservices."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class DatabaseManager:
    """Database manager for microservices."""

    def __init__(self, database_url: str, echo: bool = False):
        """Initialize database manager.

        Args:
            database_url: PostgreSQL connection URL
            echo: Whether to echo SQL statements
        """
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=NullPool,  # Each service manages its own pool
            pool_pre_ping=True,
        )
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session.

        Yields:
            AsyncSession: Database session
        """
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()

    async def create_tables(self):
        """Create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self):
        """Close database connections."""
        await self.engine.dispose()
