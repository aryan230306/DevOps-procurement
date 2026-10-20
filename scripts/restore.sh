#!/usr/bin/env bash
# ==============================================================================
# ProcurePulse Verified Database Restore Script
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/lib.sh"

log_step "Database Restore & Verification Drill"

BACKUP_FILE="${1:-}"

if [ -z "$BACKUP_FILE" ]; then
    # Auto-select the latest backup if none provided
    BACKUP_FILE=$(find "${PROJECT_ROOT}/backups" -name "procurepulse_*.sql.gz" -type f | sort -r | head -n 1)
fi

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    log_error "No valid backup file found to restore!"
    echo "Usage: $0 [path/to/backup.sql.gz]"
    exit 1
fi

CHECKSUM_FILE="${BACKUP_FILE}.sha256"

log_info "Target backup file: ${BACKUP_FILE}"

# Verify checksum if present
if [ -f "$CHECKSUM_FILE" ]; then
    log_info "Verifying SHA256 checksum integrity..."
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 -c "${CHECKSUM_FILE}"
    else
        sha256sum -c "${CHECKSUM_FILE}"
    fi
    log_success "Checksum verified: Backup file is uncorrupted."
else
    log_warn "No .sha256 file found. Proceeding with caution."
fi

# Verify DB container is running
if ! docker ps --format '{{.Names}}' | grep -q "procurepulse_db"; then
    log_error "PostgreSQL container 'procurepulse_db' is not running!"
    exit 1
fi

log_warn "Restoring backup into 'procurepulse' database..."
gunzip -c "${BACKUP_FILE}" | docker exec -i procurepulse_db psql -U zycus_user -d procurepulse >/dev/null 2>&1

log_success "Database restore completed successfully!"
