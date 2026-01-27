#!/bin/bash
# mem0 backup script - Self-contained in mem0-system repo
# Backs up Postgres + Neo4j using docker exec
# Output: /Volumes/Data/backups/mem0/daily/YYYYmmdd_HHMMSS/

set -euo pipefail

MODE="${1:-daily}"
timestamp="$(date +%Y%m%d_%H%M%S)"

BACKUP_ROOT="${MEM0_BACKUP_ROOT:-/Volumes/Data/backups/mem0}"
OUT_DIR="${BACKUP_ROOT}/${MODE}/${timestamp}"
mkdir -p "${OUT_DIR}/postgres" "${OUT_DIR}/neo4j" "${OUT_DIR}/config"

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

# =============================================================================
# BACKUP VALIDATION (prevents backing up empty database)
# =============================================================================

log "Validating backup..."

# Check 1: File size must be reasonable (> 100KB for postgres)
PG_BACKUP="${OUT_DIR}/postgres/mem0_${timestamp}.sql.gz"
PG_SIZE=$(stat -f%z "${PG_BACKUP}" 2>/dev/null || stat -c%s "${PG_BACKUP}" 2>/dev/null)

if [[ ${PG_SIZE} -lt 100000 ]]; then
  log "❌ ERROR: PostgreSQL backup too small (${PG_SIZE} bytes < 100KB)"
  log "   This indicates an empty or corrupted backup."
  log "   Backup saved but FLAGGED: ${OUT_DIR}/VALIDATION_FAILED"
  touch "${OUT_DIR}/VALIDATION_FAILED"
  exit 1
fi

# Check 2: Extract memory count from backup
log "Checking memory count in backup..."

# Count actual data rows (lines between COPY statement and terminator \.)
MEMORY_COUNT=$(gunzip -c "${PG_BACKUP}" | awk '
  /^COPY public.memories/ { copying=1; next }
  copying && /^\\.$/ { copying=0; next }
  copying { count++ }
  END { print count }
')

# Alternative method if awk fails: extract from COPY statement
if [[ ${MEMORY_COUNT} -eq 0 ]]; then
  log "⚠️  WARNING: Could not count rows with awk, trying COPY statement..."
  COPY_LINE=$(gunzip -c "${PG_BACKUP}" | grep "^COPY public.memories" | head -1)
  # Extract count from end of COPY line if present (PostgreSQL 12+ format)
  MEMORY_COUNT=$(echo "${COPY_LINE}" | awk '{print $NF}' | grep -o '[0-9]*' || echo "0")
fi

log "Memory count in backup: ${MEMORY_COUNT}"

# Check 3: Verify count is reasonable
if [[ ${MEMORY_COUNT} -eq 0 ]]; then
  log "❌ ERROR: Backup contains ZERO memories!"
  log "   This indicates database is empty or backup is corrupted."
  log "   Backup saved but FLAGGED: ${OUT_DIR}/VALIDATION_FAILED"
  echo "MEMORY_COUNT=0" > "${OUT_DIR}/VALIDATION_FAILED"

  # Send Telegram alert if configured
  if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]] && [[ -n "${TELEGRAM_CHAT_ID:-}" ]]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${TELEGRAM_CHAT_ID}" \
      -d "text=🚨 CRITICAL: mem0 backup contains ZERO memories!%0A%0ABackup: ${timestamp}%0ALocation: ${OUT_DIR}%0A%0AImmediate investigation required." \
      >/dev/null 2>&1 || true
  fi

  exit 1
fi

# Check 4: Compare with live database count
LIVE_COUNT=$(docker exec "${PG_CONTAINER}" sh -c '
  : "${POSTGRES_USER:?}" "${POSTGRES_DB:?}"
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc "SELECT COUNT(*) FROM memories"
' 2>/dev/null || echo "0")

if [[ ${LIVE_COUNT} -gt 0 ]] && [[ ${MEMORY_COUNT} -ne ${LIVE_COUNT} ]]; then
  PCT_DIFF=$(( (LIVE_COUNT - MEMORY_COUNT) * 100 / LIVE_COUNT ))
  if [[ ${PCT_DIFF#-} -gt 10 ]]; then  # Absolute value > 10%
    log "⚠️  WARNING: Backup count (${MEMORY_COUNT}) differs from live count (${LIVE_COUNT}) by ${PCT_DIFF}%"
    log "   This may indicate backup inconsistency or active writes during backup."
  fi
fi

# Create validation report
cat > "${OUT_DIR}/VALIDATION_REPORT" <<EOF
Backup Validation Report
========================
Timestamp: ${timestamp}
Backup Directory: ${OUT_DIR}

PostgreSQL Backup:
  - File: $(basename "${PG_BACKUP}")
  - Size: ${PG_SIZE} bytes ($(( PG_SIZE / 1024 / 1024 )) MB)
  - Memory Count: ${MEMORY_COUNT}
  - Live Count: ${LIVE_COUNT}
  - Status: $([ ${MEMORY_COUNT} -gt 0 ] && echo "✅ VALID" || echo "❌ FAILED")

Checksums:
  - PostgreSQL: $(cat "${PG_BACKUP}.sha256" 2>/dev/null | cut -d' ' -f1 || echo "N/A")
  - Neo4j: $(cat "${OUT_DIR}/neo4j/mem0_neo4j_${timestamp}.tar.gz.sha256" 2>/dev/null | cut -d' ' -f1 || echo "N/A")

Validation: PASSED
EOF

log "✅ Backup validation passed (${MEMORY_COUNT} memories)"

# Backup configuration files (.env) for DR
if [[ -f "${MEM0_REPO_DIR}/.env" ]]; then
  log "Backing up .env configuration..."
  cp "${MEM0_REPO_DIR}/.env" "${OUT_DIR}/config/.env.prd"
fi
if [[ -f "${MEM0_REPO_DIR}/.env.test" ]]; then
  cp "${MEM0_REPO_DIR}/.env.test" "${OUT_DIR}/config/.env.test"
fi

log "✅ mem0 backup complete: ${OUT_DIR}"
log "   Memory count: ${MEMORY_COUNT}"
log "   Validation report: ${OUT_DIR}/VALIDATION_REPORT"
