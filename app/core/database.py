"""PostgreSQL database connection"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import asyncpg
from asyncpg import Pool

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    _pool: Optional[Pool] = None
    
    @classmethod
    async def initialize(cls) -> None:
        """Initialize database connection pool"""
        if cls._pool is None:
            try:
                cls._pool = await asyncpg.create_pool(
                    settings.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    timeout=30
                )
                # Test connection
                async with cls._pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                logger.info("Database pool initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database pool: {e}")
                cls._pool = None  # Don't raise, allow app to run without DB
    
    @classmethod
    async def close(cls) -> None:
        """Close database connection pool"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            logger.info("Database pool closed")
    
    @classmethod
    def get_pool(cls) -> Optional[Pool]:
        return cls._pool


@asynccontextmanager
async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get database connection from pool"""
    pool = DatabaseManager.get_pool()
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    
    async with pool.acquire() as connection:
        yield connection
