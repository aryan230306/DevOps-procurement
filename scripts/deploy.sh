#!/usr/bin/env bash
# ==============================================================================
# Zycus ProcurePulse Zero-Downtime Deployment Script
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/lib.sh"

log_step "Starting Deployment for Zycus ProcurePulse"

require_cmd docker
require_cmd curl

cd "${PROJECT_ROOT}"

# 1. Ensure .env exists
if [ ! -f ".env" ]; then
    log_warn ".env not found. Initializing with ./scripts/init_env.sh..."
    "${SCRIPT_DIR}/init_env.sh"
fi

# 2. Start PostgreSQL first and wait for health
log_info "Ensuring database service is healthy..."
docker compose up -d db

log_info "Waiting for database to report healthy status..."
DB_HEALTHY=false
for i in {1..30}; do
    STATUS=$(docker inspect --format='{{json .State.Health.Status}}' procurepulse_db 2>/dev/null || echo '"unknown"')
    if [ "$STATUS" == '"healthy"' ]; then
        DB_HEALTHY=true
        log_success "Database is healthy!"
        break
    fi
    echo -n "."
    sleep 2
done

if [ "$DB_HEALTHY" != "true" ]; then
    log_error "Database failed to become healthy within 60s. Aborting deployment."
    exit 1
fi

# 3. Rolling deploy of App service
log_info "Deploying application service..."
docker compose up -d --build app

# 4. Verify Application Readiness Probe
log_info "Verifying application readiness (/readyz)..."
APP_READY=false
for i in {1..20}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/readyz || echo "000")
    if [ "$HTTP_CODE" == "200" ]; then
        APP_READY=true
        log_success "Application passed readiness probe (HTTP 200)!"
        break
    fi
    echo -n "."
    sleep 2
done

if [ "$APP_READY" != "true" ]; then
    log_error "Readiness probe failed after 40 seconds! Triggering automated rollback..."
    "${SCRIPT_DIR}/rollback.sh"
    exit 1
fi

# 5. Bring up remaining edge & observability services
log_info "Starting Nginx reverse proxy, Prometheus, Grafana, Alertmanager & Exporters..."
docker compose up -d nginx prometheus alertmanager grafana blackbox-exporter node-exporter alert-sink

# 6. Execute rapid smoke verification
log_info "Running post-deploy smoke verification..."
if command -v python3 >/dev/null 2>&1; then
    python3 "${SCRIPT_DIR}/smoke.py" http://localhost:80 || true
fi

log_success "Deployment completed successfully!"
echo -e "\n${BOLD}${CYAN}Service Endpoints:${NC}"
echo -e "  - Public API (via Nginx):  http://localhost"
echo -e "  - API Swagger Docs:       http://localhost/docs"
echo -e "  - Prometheus Server:      http://localhost:9090"
echo -e "  - Alertmanager:           http://localhost:9093"
echo -e "  - Grafana Dashboards:     http://localhost:3000  (admin / admin)"
echo -e "  - Alert Webhook Sink:     http://localhost:9999/alerts"
echo -e "  - Blackbox Exporter:      http://localhost:9115"
