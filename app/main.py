"""Zycus ProcurePulse FastAPI Application Entrypoint."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app import __version__
from app.api.analytics import router as analytics_router
from app.api.chaos import router as chaos_router
from app.api.health import router as health_router
from app.api.requisitions import router as requisitions_router
from app.config import settings
from app.database import init_db
from app.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_FLIGHT,
    HTTP_REQUESTS_TOTAL,
    get_metrics_payload,
)
from app.ui import DASHBOARD_HTML

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("procurepulse")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown lifecycle events."""
    logger.info(f"Starting {settings.APP_NAME} v{__version__} ({settings.APP_ENV})...")
    try:
        await init_db()
        logger.info("Database connectivity established.")
    except Exception as exc:
        logger.error(f"Startup database initialization error: {exc}")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise Procurement Requisition & Purchase Order API with Built-in SRE Observability & Chaos Injection.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    """Intercepts all HTTP traffic to record RED metrics with route normalization."""
    # Exclude metrics and health scrapes from polluting latency histograms if needed,
    # or keep them to verify scraping works
    endpoint = request.url.path
    method = request.method

    # Normalize parameterized routes to prevent cardinality explosion in Prometheus
    # e.g., /api/v1/requisitions/123 -> /api/v1/requisitions/{id}
    parts = endpoint.split("/")
    if len(parts) >= 5 and parts[1] == "api" and parts[2] == "v1" and parts[3] == "requisitions" and parts[4].isdigit():
        parts[4] = "{id}"
        endpoint = "/".join(parts)

    HTTP_REQUESTS_IN_FLIGHT.inc()
    start_time = time.perf_counter()

    try:
        response: Response = await call_next(request)
        status_code = str(response.status_code)
    except Exception:
        status_code = "500"
        raise
    finally:
        duration = time.perf_counter() - start_time
        HTTP_REQUESTS_IN_FLIGHT.dec()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

    return response


# ---------------------------------------------------------
# Observability Metrics Endpoint
# ---------------------------------------------------------
@app.get(
    "/metrics",
    summary="Prometheus Metrics Scrape Endpoint",
    tags=["Diagnostics & Observability"],
)
async def metrics():
    """Returns Prometheus exposition formatted metrics for scraping."""
    content, content_type = get_metrics_payload()
    return Response(content=content, media_type=content_type)


# ---------------------------------------------------------
# Mount Sub-Routers
# ---------------------------------------------------------
app.include_router(health_router)
app.include_router(requisitions_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)
app.include_router(chaos_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["General"], response_class=HTMLResponse)
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return JSONResponse(
            content={
                "service": settings.APP_NAME,
                "version": __version__,
                "documentation": "/docs",
                "health": "/healthz",
                "readiness": "/readyz",
                "metrics": "/metrics",
                "api_v1": {
                    "requisitions": f"{settings.API_PREFIX}/requisitions",
                    "analytics": f"{settings.API_PREFIX}/analytics/spend",
                    "chaos": f"{settings.API_PREFIX}/chaos/status",
                },
            }
        )
    return HTMLResponse(content=DASHBOARD_HTML)
