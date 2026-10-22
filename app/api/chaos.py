"""Chaos engineering control endpoints for failure injection and Game Day runs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.chaos.engine import chaos_engine
from app.config import settings
from app.schemas import (
    ChaosErrorRequest,
    ChaosLatencyRequest,
    ChaosMemoryRequest,
)

router = APIRouter(prefix="/chaos", tags=["Chaos Engineering"])


def require_chaos_control(x_chaos_token: str | None = Header(default=None)) -> None:
    """Require an explicit token before mutating chaos state in production."""
    if settings.APP_ENV != "production":
        return
    if not settings.CHAOS_CONTROL_TOKEN or x_chaos_token != settings.CHAOS_CONTROL_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chaos controls are restricted in production.",
        )


@router.get("/status", summary="Get Chaos Engine Status")
async def get_chaos_status() -> dict[str, Any]:
    return chaos_engine.get_status()


@router.post("/latency", summary="Inject Upstream Latency")
async def inject_latency(
    payload: ChaosLatencyRequest, _: None = Depends(require_chaos_control)
):
    chaos_engine.arm_latency(
        delay_seconds=payload.delay_seconds,
        probability=payload.probability,
    )
    return {
        "status": "armed",
        "fault": "latency",
        "delay_seconds": payload.delay_seconds,
        "probability": payload.probability,
    }


@router.post("/error", summary="Inject HTTP Error Bursts (Burn SLO Error Budget)")
async def inject_errors(
    payload: ChaosErrorRequest, _: None = Depends(require_chaos_control)
):
    chaos_engine.arm_error_spike(
        probability=payload.probability,
        status_code=payload.status_code,
        message=payload.message,
    )
    return {
        "status": "armed",
        "fault": "error_spike",
        "status_code": payload.status_code,
        "probability": payload.probability,
    }


@router.post("/db-offline", summary="Simulate Database Outage")
async def simulate_db_offline(
    offline: bool = True, _: None = Depends(require_chaos_control)
):
    chaos_engine.arm_db_offline(offline=offline)
    return {
        "status": "armed" if offline else "disarmed",
        "fault": "db_offline",
        "offline": offline,
    }


@router.post("/memory-leak", summary="Simulate Memory Leak")
async def simulate_memory_leak(
    payload: ChaosMemoryRequest, _: None = Depends(require_chaos_control)
):
    total_leaked_mb = chaos_engine.simulate_memory_leak(megabytes=payload.megabytes)
    return {
        "status": "triggered",
        "fault": "memory_leak",
        "allocated_chunk_mb": payload.megabytes,
        "total_leaked_mb": total_leaked_mb,
    }


@router.post("/reset", summary="Disarm All Chaos Experiments (Restore Baseline)")
async def reset_chaos(_: None = Depends(require_chaos_control)):
    chaos_engine.reset()
    return {
        "status": "reset",
        "message": "All chaos experiments disarmed. System operating at nominal baseline.",
    }
