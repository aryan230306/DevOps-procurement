"""Tests for chaos engineering failure injection mechanisms."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chaos_status_and_reset(client: AsyncClient):
    res = await client.get("/api/v1/chaos/status")
    assert res.status_code == 200
    status_data = res.json()
    assert status_data["enabled"] is True
    assert status_data["latency"]["active"] is False

    reset_res = await client.post("/api/v1/chaos/reset")
    assert reset_res.status_code == 200
    assert "disarmed" in reset_res.json()["message"]


@pytest.mark.asyncio
async def test_production_chaos_mutations_require_control_token(client: AsyncClient, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "CHAOS_CONTROL_TOKEN", "test-token")

    denied = await client.post(
        "/api/v1/chaos/error",
        json={"probability": 1.0, "status_code": 500},
    )
    assert denied.status_code == 403

    allowed = await client.post(
        "/api/v1/chaos/error",
        headers={"X-Chaos-Token": "test-token"},
        json={"probability": 1.0, "status_code": 500},
    )
    assert allowed.status_code == 200
    await client.post("/api/v1/chaos/reset", headers={"X-Chaos-Token": "test-token"})


@pytest.mark.asyncio
async def test_chaos_error_injection(client: AsyncClient):
    # Arm error spike: 100% chance of HTTP 500
    arm_res = await client.post(
        "/api/v1/chaos/error",
        json={
            "probability": 1.0,
            "status_code": 500,
            "message": "Chaos Injected: Critical Database Exhaustion",
        },
    )
    assert arm_res.status_code == 200

    # Normal API call should now fail with 500
    failing_req = await client.get("/api/v1/requisitions/")
    assert failing_req.status_code == 500
    assert "Chaos Injected" in failing_req.json()["detail"]

    # Reset chaos
    await client.post("/api/v1/chaos/reset")

    # API call should recover immediately
    recovered_req = await client.get("/api/v1/requisitions/")
    assert recovered_req.status_code == 200


@pytest.mark.asyncio
async def test_chaos_db_offline_affects_readiness(client: AsyncClient):
    # Turn DB offline
    arm_db = await client.post("/api/v1/chaos/db-offline?offline=true")
    assert arm_db.status_code == 200

    # /healthz should still be UP (process is alive)
    liveness = await client.get("/healthz")
    assert liveness.status_code == 200

    # /readyz should fail with 503 (not ready to accept traffic)
    readiness = await client.get("/readyz")
    assert readiness.status_code == 503
    assert readiness.json()["ready"] is False
    assert readiness.json()["database"]["latency_ms"] is None

    # Disarm
    await client.post("/api/v1/chaos/db-offline?offline=false")
    ready_again = await client.get("/readyz")
    assert ready_again.status_code == 200
    assert ready_again.json()["ready"] is True
