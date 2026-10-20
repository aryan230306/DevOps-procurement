#!/usr/bin/env bash
# ==============================================================================
# Zycus ProcurePulse Automated Rollback Script
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/lib.sh"

log_step "Initiating Emergency Rollback for Zycus ProcurePulse"

cd "${PROJECT_ROOT}"

# Disarm any chaos injection immediately
log_info "Disarming any active chaos faults..."
curl -s -X POST http://localhost:8000/api/v1/chaos/reset >/dev/null 2>&1 || true

# Restart previous stable app container
log_warn "Restarting application container with previous stable image..."
docker compose restart app || docker compose up -d app

# Verify recovery
log_info "Verifying service recovery..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthz || echo "000")

if [ "$HTTP_CODE" == "200" ]; then
    log_success "Rollback successful! Service is responsive (HTTP 200)."
else
    log_error "Service is still unresponsive after rollback! Check logs: 'docker compose logs app'"
    exit 1
fi
