#!/usr/bin/env bash
# ==============================================================================
# Zycus ProcurePulse Container Image Builder
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${SCRIPT_DIR}/lib.sh"

TAG="${1:-latest}"
IMAGE_NAME="zycus/procurepulse"

log_step "Building Zycus ProcurePulse Container Image [${IMAGE_NAME}:${TAG}]"

require_cmd docker

log_info "Executing multi-stage build from ${PROJECT_ROOT}/Dockerfile..."
docker build \
    --tag "${IMAGE_NAME}:${TAG}" \
    --tag "${IMAGE_NAME}:latest" \
    --file "${PROJECT_ROOT}/Dockerfile" \
    "${PROJECT_ROOT}"

log_success "Build completed successfully!"
docker images | grep "zycus/procurepulse" || true
