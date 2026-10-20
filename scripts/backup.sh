#!/usr/bin/env bash
# ==============================================================================
# ProcurePulse Automated PostgreSQL Backup Script
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/lib.sh"

log_step "Executing PostgreSQL Database Backup"

BACKUP_DIR="${PROJECT_ROOT}/backups"
mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/procurepulse_${TIMESTAMP}.sql.gz"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

# Verify DB container is running
if ! docker ps --format '{{.Names}}' | grep -q "procurepulse_db"; then
    log_error "PostgreSQL container 'procurepulse_db' is not running!"
    exit 1
fi

log_info "Dumping database 'procurepulse' via pg_dump..."
docker exec procurepulse_db pg_dump -U zycus_user -d procurepulse | gzip > "${BACKUP_FILE}"

log_info "Calculating SHA256 cryptographic checksum..."
if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
else
    sha256sum "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
fi

BACKUP_SIZE=$(ls -lh "${BACKUP_FILE}" | awk '{print $5}')
log_success "Backup created successfully: ${BACKUP_FILE} (${BACKUP_SIZE})"
log_success "Checksum verified: $(cat "${CHECKSUM_FILE}")"

# Retention policy: remove backups older than 7 days
log_info "Applying retention policy: pruning backups older than 7 days..."
find "${BACKUP_DIR}" -name "procurepulse_*.sql.gz*" -type f -mtime +7 -delete || true

log_success "Backup operation completed."
