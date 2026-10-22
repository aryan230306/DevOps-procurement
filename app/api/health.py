"""Health and readiness diagnostic probes for Kubernetes, Docker, and Blackbox Exporter."""

from datetime import datetime, timezone

from fastapi import APIRouter, Response, status

from app import __version__
from app.chaos.engine import chaos_engine
from app.config import settings
from app.database import check_db_health
from app.schemas import DatabaseHealthDetail, HealthResponse, ReadinessResponse

router = APIRouter(tags=["Diagnostics & Observability"])


@router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Liveness Probe",
    description="Returns HTTP 200 if the FastAPI application process is alive and responsive.",
)
async def liveness_probe():
    return HealthResponse(
        status="UP",
        version=__version__,
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
    )


@router.get(
    "/readyz",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Validates downstream dependencies (e.g., PostgreSQL connection). Returns 503 if not ready for traffic.",
)
async def readiness_probe(response: Response):
    # Check if chaos engine has intercepted database traffic
    if chaos_engine.is_enabled and chaos_engine._db_offline:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            ready=False,
            status="DEGRADED",
            database=DatabaseHealthDetail(
                connected=False,
                latency_ms=None,
                message="Chaos Injected: Database offline",
            ),
            timestamp=datetime.now(timezone.utc),
        )

    # Perform active DB health check
    is_healthy, latency_ms, message = await check_db_health(timeout_seconds=2.0)

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        ready=is_healthy,
        status="READY" if is_healthy else "UNAVAILABLE",
        database=DatabaseHealthDetail(
            connected=is_healthy,
            latency_ms=latency_ms,
            message=message,
        ),
        timestamp=datetime.now(timezone.utc),
    )
