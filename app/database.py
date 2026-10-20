"""Database engine configuration, connection pooling, and lifecycle hooks."""

import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.metrics import (
    DB_CONNECTION_ERRORS_TOTAL,
    DB_POOL_CHECKED_OUT,
    DB_POOL_SIZE,
)
from app.models import Base

logger = logging.getLogger(__name__)

# Determine if running with SQLite (for fast local dev/testing) or PostgreSQL
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs = {
    "echo": settings.DEBUG,
}

if not is_sqlite:
    engine_kwargs.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "pool_pre_ping": True,
        }
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Creates database schema if tables do not exist."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")
        if not is_sqlite:
            DB_POOL_SIZE.set(settings.DB_POOL_SIZE)
    except Exception as exc:
        DB_CONNECTION_ERRORS_TOTAL.inc()
        logger.error(f"Failed to initialize database: {exc}")
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injector providing an async database session per request."""
    if not is_sqlite and hasattr(engine.pool, "checkedout"):
        DB_POOL_CHECKED_OUT.set(engine.pool.checkedout())

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            if not is_sqlite and hasattr(engine.pool, "checkedout"):
                DB_POOL_CHECKED_OUT.set(engine.pool.checkedout())


async def check_db_health(timeout_seconds: float = 2.0) -> tuple[bool, float, str]:
    """Executes a synthetic health check query against the database engine.

    Returns:
        (is_healthy, response_time_ms, message)
    """
    loop = asyncio.get_event_loop()
    start_time = loop.time()

    async def _query():
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar()

    try:
        row = await asyncio.wait_for(_query(), timeout=timeout_seconds)
        latency_ms = (loop.time() - start_time) * 1000.0
        if row == 1:
            return True, round(latency_ms, 2), "healthy"
        return False, round(latency_ms, 2), "invalid query result"
    except TimeoutError:
        DB_CONNECTION_ERRORS_TOTAL.inc()
        latency_ms = (loop.time() - start_time) * 1000.0
        return False, round(latency_ms, 2), f"timeout after {timeout_seconds}s"
    except Exception as exc:
        DB_CONNECTION_ERRORS_TOTAL.inc()
        latency_ms = (loop.time() - start_time) * 1000.0
        return False, round(latency_ms, 2), str(exc)
