"""In-process Chaos Engineering Engine for Zycus ProcurePulse.

Allows SRE teams to safely simulate real-world production outages:
- Upstream latency spikes
- HTTP 500 error bursts (burning SLO error budgets)
- Database unavailability & connection dropouts
- Memory & CPU resource pressure
"""

import asyncio
import logging
import random
from typing import Any

from fastapi import HTTPException, status

from app.metrics import CHAOS_ACTIVE_FLAG, CHAOS_FAULTS_INJECTED_TOTAL

logger = logging.getLogger(__name__)


class ChaosEngine:
    """Manages active chaos experiments and injects deterministic failure modes."""

    def __init__(self):
        self._enabled: bool = True
        self._latency_delay: float = 0.0
        self._latency_probability: float = 0.0

        self._error_status_code: int = 500
        self._error_probability: float = 0.0
        self._error_message: str = "Chaos Injected: Service Unavailable"

        self._db_offline: bool = False
        self._leak_buffer: list[bytes] = []

        # Initialize all telemetry flags to 0
        for fault in ["latency", "error_spike", "db_offline", "memory_leak"]:
            CHAOS_ACTIVE_FLAG.labels(fault_type=fault).set(0)

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self.reset()

    def arm_latency(self, delay_seconds: float, probability: float = 1.0) -> None:
        """Injects synthetic latency into API endpoints."""
        self._latency_delay = max(0.0, delay_seconds)
        self._latency_probability = max(0.0, min(1.0, probability))
        is_active = 1 if self._latency_delay > 0 and self._latency_probability > 0 else 0
        CHAOS_ACTIVE_FLAG.labels(fault_type="latency").set(is_active)
        logger.warning(
            f"Chaos Armed: Latency injection {self._latency_delay}s (prob: {self._latency_probability})"
        )

    def arm_error_spike(
        self,
        probability: float = 1.0,
        status_code: int = 500,
        message: str = "Chaos Injected: Internal Server Error",
    ) -> None:
        """Forces HTTP error responses to test SLO multi-burn-rate alerts."""
        self._error_probability = max(0.0, min(1.0, probability))
        self._error_status_code = status_code
        self._error_message = message
        is_active = 1 if self._error_probability > 0 else 0
        CHAOS_ACTIVE_FLAG.labels(fault_type="error_spike").set(is_active)
        logger.warning(
            f"Chaos Armed: Error injection status {status_code} (prob: {self._error_probability})"
        )

    def arm_db_offline(self, offline: bool = True) -> None:
        """Simulates complete database connection drop."""
        self._db_offline = offline
        CHAOS_ACTIVE_FLAG.labels(fault_type="db_offline").set(1 if offline else 0)
        logger.warning(f"Chaos Armed: Database offline simulation set to {offline}")

    def simulate_memory_leak(self, megabytes: int = 50) -> int:
        """Allocates memory chunks to simulate a memory leak."""
        chunk = b"X" * (megabytes * 1024 * 1024)
        self._leak_buffer.append(chunk)
        CHAOS_FAULTS_INJECTED_TOTAL.labels(fault_type="memory_leak").inc()
        CHAOS_ACTIVE_FLAG.labels(fault_type="memory_leak").set(1)
        total_mb = sum(len(c) for c in self._leak_buffer) // (1024 * 1024)
        logger.warning(f"Chaos Triggered: Allocated {megabytes}MB (Total leak: {total_mb}MB)")
        return total_mb

    async def maybe_inject_latency(self) -> None:
        """Conditionally delays the current coroutine."""
        if not self._enabled:
            return
        if self._latency_delay > 0 and random.random() < self._latency_probability:
            CHAOS_FAULTS_INJECTED_TOTAL.labels(fault_type="latency").inc()
            logger.info(f"Injecting synthetic latency: {self._latency_delay}s")
            await asyncio.sleep(self._latency_delay)

    def maybe_inject_error(self) -> None:
        """Conditionally raises an HTTP error."""
        if not self._enabled:
            return
        if self._error_probability > 0 and random.random() < self._error_probability:
            CHAOS_FAULTS_INJECTED_TOTAL.labels(fault_type="error_spike").inc()
            logger.info(f"Injecting synthetic HTTP {self._error_status_code} error")
            raise HTTPException(
                status_code=self._error_status_code,
                detail=self._error_message,
            )

    def check_db_interception(self) -> None:
        """Throws database failure if DB chaos is armed."""
        if self._enabled and self._db_offline:
            CHAOS_FAULTS_INJECTED_TOTAL.labels(fault_type="db_offline").inc()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection dropped: ConnectionRefusedError(PostgreSQL host unreachable)",
            )

    def reset(self) -> None:
        """Disarms all active chaos experiments."""
        self._latency_delay = 0.0
        self._latency_probability = 0.0
        self._error_probability = 0.0
        self._db_offline = False
        self._leak_buffer.clear()

        for fault in ["latency", "error_spike", "db_offline", "memory_leak"]:
            CHAOS_ACTIVE_FLAG.labels(fault_type=fault).set(0)

        logger.info("Chaos Engine: All experiments disarmed. System nominal.")

    def get_status(self) -> dict[str, Any]:
        """Returns the current state of chaos experiments."""
        total_leaked_mb = sum(len(c) for c in self._leak_buffer) // (1024 * 1024)
        return {
            "enabled": self._enabled,
            "latency": {
                "active": self._latency_delay > 0 and self._latency_probability > 0,
                "delay_seconds": self._latency_delay,
                "probability": self._latency_probability,
            },
            "error_spike": {
                "active": self._error_probability > 0,
                "probability": self._error_probability,
                "status_code": self._error_status_code,
                "message": self._error_message,
            },
            "db_offline": {
                "active": self._db_offline,
            },
            "memory_leak": {
                "active": total_leaked_mb > 0,
                "leaked_megabytes": total_leaked_mb,
            },
        }


chaos_engine = ChaosEngine()
