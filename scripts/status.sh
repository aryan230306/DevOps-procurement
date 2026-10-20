#!/usr/bin/env bash
# ==============================================================================
# Zycus ProcurePulse Real-Time Health & Status CLI
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/lib.sh"

log_step "Zycus ProcurePulse Production Status Overview"

cd "${PROJECT_ROOT}"

echo -e "\n${BOLD}${CYAN}[1] Container Infrastructure Status:${NC}"
docker compose ps 2>/dev/null || echo "Docker daemon not running or containers not created."

echo -e "\n${BOLD}${CYAN}[2] Application Health & Readiness:${NC}"
HEALTH_JSON=$(curl -s http://localhost:8000/healthz 2>/dev/null || echo "")
READINESS_JSON=$(curl -s http://localhost:8000/readyz 2>/dev/null || echo "")

if [ -n "$HEALTH_JSON" ]; then
    echo -e "  Liveness Probe (/healthz):   ${GREEN}UP${NC} -> $HEALTH_JSON"
else
    echo -e "  Liveness Probe (/healthz):   ${RED}DOWN (Cannot reach :8000)${NC}"
fi

if [ -n "$READINESS_JSON" ]; then
    echo -e "  Readiness Probe (/readyz):   ${GREEN}ONLINE${NC} -> $READINESS_JSON"
else
    echo -e "  Readiness Probe (/readyz):   ${RED}DOWN${NC}"
fi

echo -e "\n${BOLD}${CYAN}[3] Chaos Engine State:${NC}"
CHAOS_STATUS=$(curl -s http://localhost:8000/api/v1/chaos/status 2>/dev/null || echo "")
if [ -n "$CHAOS_STATUS" ]; then
    echo -e "  $CHAOS_STATUS"
else
    echo -e "  ${YELLOW}App not running or chaos disabled.${NC}"
fi

echo -e "\n${BOLD}${CYAN}[4] Active Alerts in Alertmanager:${NC}"
ALERTS_JSON=$(curl -s http://localhost:9093/api/v2/alerts 2>/dev/null || echo "")
if [ -n "$ALERTS_JSON" ] && [ "$ALERTS_JSON" != "[]" ]; then
    echo -e "  ${RED}Active Alerting Events Firing:${NC}"
    echo "$ALERTS_JSON" | grep -E '"alertname"|"severity"|"summary"' || echo "$ALERTS_JSON"
else
    echo -e "  ${GREEN}No active alerts firing. All systems within SLO thresholds.${NC}"
fi
