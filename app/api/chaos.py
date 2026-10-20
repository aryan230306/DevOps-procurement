"""Chaos engineering control endpoints for failure injection and Game Day runs."""

from typing import Any

from fastapi import APIRouter

from app.chaos.engine import chaos_engine
from app.schemas import (
    ChaosErrorRequest,
    ChaosLatencyRequest,
    ChaosMemoryRequest,
)

router = APIRouter(prefix="/chaos", tags=["Chaos Engineering"])


@router.get("/status", summary="Get Chaos Engine Status")
async def get_chaos_status() -> dict[str, Any]:
    return chaos_engine.get_status()


@router.post("/latency", summary="Inject Upstream Latency")
async def inject_latency(payload: ChaosLatencyRequest):
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
async def inject_errors(payload: ChaosErrorRequest):
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
async def simulate_db_offline(offline: bool = True):
    chaos_engine.arm_db_offline(offline=offline)
    return {
        "status": "armed" if offline else "disarmed",
        "fault": "db_offline",
        "offline": offline,
    }


@router.post("/memory-leak", summary="Simulate Memory Leak")
async def simulate_memory_leak(payload: ChaosMemoryRequest):
    total_leaked_mb = chaos_engine.simulate_memory_leak(megabytes=payload.megabytes)
    return {
        "status": "triggered",
        "fault": "memory_leak",
        "allocated_chunk_mb": payload.megabytes,
        "total_leaked_mb": total_leaked_mb,
    }


@router.post("/reset", summary="Disarm All Chaos Experiments (Restore Baseline)")
async def reset_chaos():
    chaos_engine.reset()
    return {
        "status": "reset",
        "message": "All chaos experiments disarmed. System operating at nominal baseline.",
    }
