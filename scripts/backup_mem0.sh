#!/bin/bash
# mem0 backup script - Self-contained in mem0-system repo
# Backs up Postgres + Neo4j using docker exec
# Output: /Volumes/Data/backups/mem0/daily/YYYYmmdd_HHMMSS/

set -euo pipefail

MODE="${1:-daily}"
timestamp="$(date +%Y%m%d_%H%M%S)"

BACKUP_ROOT="${MEM0_BACKUP_ROOT:-/Volumes/Data/backups/mem0}"
OUT_DIR="${BACKUP_ROOT}/${MODE}/${timestamp}"
mkdir -p "${OUT_DIR}/postgres" "${OUT_DIR}/neo4j"

PG_CONTAINER="${MEM0_POSTGRES_CONTAINER:-mem0_postgres_prd}"
NEO4J_CONTAINER="${MEM0_NEO4J_CONTAINER:-mem0_neo4j_prd}"
MEM0_REPO_DIR="${MEM0_REPO_DIR:-/Volumes/Data/ai_projects/mem0-system}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

container_exists() { docker ps --format '{{.Names}}' | grep -q "^$1$"; }

# Self-heal: try to start PRD if containers are missing
if ! container_exists "${PG_CONTAINER}"; then
  if [[ -x "${MEM0_REPO_DIR}/deploy_prd.sh" && -f "${MEM0_REPO_DIR}/.env" ]]; then
    log "mem0 containers missing; attempting to start PRD via ${MEM0_REPO_DIR}/deploy_prd.sh"
    (cd "${MEM0_REPO_DIR}" && ./deploy_prd.sh up) || true
    sleep 10
  fi
fi

# Backup if containers are running
if container_exists "${PG_CONTAINER}" && container_exists "${NEO4J_CONTAINER}"; then
  log "Backing up mem0 postgres from container: ${PG_CONTAINER}"
  docker exec "${PG_CONTAINER}" sh -lc '
    set -e
    : "${POSTGRES_USER:?}" "${POSTGRES_DB:?}"
    pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip -9
  ' > "${OUT_DIR}/postgres/mem0_${timestamp}.sql.gz"
  
  log "Backing up mem0 neo4j from container: ${NEO4J_CONTAINER}"
  docker exec "${NEO4J_CONTAINER}" sh -lc 'tar -czf - /data' \
    > "${OUT_DIR}/neo4j/mem0_neo4j_${timestamp}.tar.gz"
else
  log "ERROR: mem0 containers not running (expected ${PG_CONTAINER}, ${NEO4J_CONTAINER})"
  exit 1
fi

# Generate checksums
if command -v shasum >/dev/null 2>&1; then
  shasum -a 256 "${OUT_DIR}/postgres/mem0_${timestamp}.sql.gz" > "${OUT_DIR}/postgres/mem0_${timestamp}.sql.gz.sha256"
  shasum -a 256 "${OUT_DIR}/neo4j/mem0_neo4j_${timestamp}.tar.gz" > "${OUT_DIR}/neo4j/mem0_neo4j_${timestamp}.tar.gz.sha256"
fi

log "✅ mem0 backup complete: ${OUT_DIR}"
