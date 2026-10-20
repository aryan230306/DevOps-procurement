#!/usr/bin/env bash
# ==============================================================================
# Zycus ProcurePulse Environment Initializer
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/lib.sh"

log_step "Initializing Zycus ProcurePulse Environment"

ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/.env.example"

if [ -f "$ENV_FILE" ]; then
    log_warn ".env already exists at ${ENV_FILE}. Keeping existing configuration."
else
    log_info "Creating .env from .env.example..."
    cp "$ENV_EXAMPLE" "$ENV_FILE"

    # Generate secure random secret key
    RANDOM_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -hex 32)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=${RANDOM_SECRET}/g" "$ENV_FILE"
    else
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=${RANDOM_SECRET}/g" "$ENV_FILE"
    fi
    log_success "Generated new cryptographic SECRET_KEY in .env"
fi

# Ensure necessary host directories exist
mkdir -p "${PROJECT_ROOT}/monitoring/grafana/dashboards"
mkdir -p "${PROJECT_ROOT}/backups"

log_success "Environment initialization complete! Run './scripts/build.sh' or 'docker compose up -d' next."
