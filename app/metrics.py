"""Prometheus metrics instrumentation for Zycus ProcurePulse.

Exposes standard RED metrics (Rate, Errors, Duration), database pool stats,
procurement domain business KPIs, and chaos testing telemetry.
"""

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# ---------------------------------------------------------
# HTTP Traffic & RED Metrics (System Observability)
# ---------------------------------------------------------
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total count of HTTP requests processed by endpoint and status code.",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Latency distribution of HTTP requests in seconds.",
    ["method", "endpoint"],
    buckets=[
        0.005, 0.01, 0.025, 0.05, 0.075, 0.1,
        0.15, 0.2, 0.25, 0.3, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0
    ],
)

HTTP_REQUESTS_IN_FLIGHT = Gauge(
    "http_requests_in_flight",
    "Current number of active in-flight HTTP requests.",
)

# ---------------------------------------------------------
# Procurement Domain Business KPIs (Zycus Core Domain)
# ---------------------------------------------------------
REQUISITIONS_CREATED_TOTAL = Counter(
    "procurement_requisitions_created_total",
    "Total number of procurement requisitions created.",
    ["department", "currency"],
)

REQUISITION_VALUE_TOTAL = Counter(
    "procurement_requisition_value_total",
    "Total cumulative monetary value of created requisitions.",
    ["department", "currency"],
)

REQUISITIONS_BY_STATE = Gauge(
    "procurement_requisitions_by_state",
    "Current count of requisitions in each lifecycle state.",
    ["state"],
)

APPROVALS_PROCESSED_TOTAL = Counter(
    "procurement_approvals_processed_total",
    "Total number of requisitions reviewed by approvers.",
    ["decision", "approver_role"],
)

# ---------------------------------------------------------
# Database Health & Connection Pool Metrics
# ---------------------------------------------------------
DB_POOL_SIZE = Gauge(
    "db_pool_size",
    "Configured maximum size of the database connection pool.",
)

DB_POOL_CHECKED_OUT = Gauge(
    "db_pool_checked_out",
    "Number of database connections currently in use by worker tasks.",
)

DB_CONNECTION_ERRORS_TOTAL = Counter(
    "db_connection_errors_total",
    "Cumulative count of database connection errors and timeouts.",
)

# ---------------------------------------------------------
# Chaos Telemetry & Failure Injection
# ---------------------------------------------------------
CHAOS_FAULTS_INJECTED_TOTAL = Counter(
    "chaos_faults_injected_total",
    "Count of chaos faults triggered during game day exercises.",
    ["fault_type"],
)

CHAOS_ACTIVE_FLAG = Gauge(
    "chaos_active_flag",
    "Indicates whether a specific chaos fault is currently armed (1) or disarmed (0).",
    ["fault_type"],
)


def get_metrics_payload() -> tuple[bytes, str]:
    """Serializes all registered Prometheus metrics for the /metrics scrape endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
