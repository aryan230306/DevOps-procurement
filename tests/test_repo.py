"""Tests for database repository layer and connection health probes."""

import pytest

from app.database import check_db_health, init_db


@pytest.mark.asyncio
async def test_database_health_check_nominal():
    # In nominal state, health check should return healthy with latency in milliseconds
    is_healthy, latency_ms, message = await check_db_health(timeout_seconds=2.0)
    assert is_healthy is True
    assert latency_ms >= 0.0
    assert message == "healthy"


@pytest.mark.asyncio
async def test_database_init_idempotent():
    # Running init_db multiple times should be safe and idempotent
    await init_db()
    await init_db()
