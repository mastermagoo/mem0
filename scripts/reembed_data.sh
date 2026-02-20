#!/bin/bash
#
# Re-embed all memories with current embedding model
# Use when switching embedding providers (e.g., OpenAI → Ollama)
# This extracts text content and re-adds it to regenerate embeddings
#

set -euo pipefail

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-mem0_postgres_prd}"
POSTGRES_USER="${POSTGRES_USER:-mem0_user_prd}"
POSTGRES_DB="${POSTGRES_DB:-mem0_prd}"
MEM0_URL="${MEM0_URL:-http://localhost:8889}"
BATCH_SIZE="${BATCH_SIZE:-10}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Check if mem0 server is responding
if ! curl -sf "${MEM0_URL}/health" > /dev/null; then
    log "ERROR: mem0 server not responding at ${MEM0_URL}"
    log "Start server with: cd /Volumes/Data/ai_projects/mem0-system && docker compose -f docker-compose.prd.yml up -d"
    exit 1
fi

log "Starting re-embedding process..."
log "This will take approximately 30-45 minutes for 2000 memories"

# Get total count
TOTAL=$(docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc \
    "SELECT COUNT(*) FROM memories;")

log "Total memories to re-embed: ${TOTAL}"

if [ "${TOTAL}" -eq 0 ]; then
    log "ERROR: No memories found in database"
    exit 1
fi

# Create temporary directory for export
TMP_DIR="/tmp/mem0_reembed_$$"
mkdir -p "${TMP_DIR}"
trap "rm -rf ${TMP_DIR}" EXIT

log "Exporting memory data..."

# Export all memories (content and user_id only, skip metadata to avoid JSON parsing issues)
docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAF'|' -c "
    SELECT
        id,
        payload->>'data' as content,
        payload->>'user_id' as user_id
    FROM memories
    ORDER BY id
" > "${TMP_DIR}/memories_export.txt"

log "Exported ${TOTAL} memories"
log "Creating backup of current data..."

# Backup current table (in case something goes wrong)
docker exec "${POSTGRES_CONTAINER}" sh -c "
    pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t memories | gzip -9
" > "${TMP_DIR}/pre_reembed_backup.sql.gz"

log "Backup created: ${TMP_DIR}/pre_reembed_backup.sql.gz"
log "Dropping and recreating memories table to reset embeddings..."

# Drop and recreate table (mem0 will auto-recreate with correct dimensions on first add)
docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
    DROP TABLE IF EXISTS memories CASCADE;
    DROP TABLE IF EXISTS memories_1536 CASCADE;
    DROP TABLE IF EXISTS memories_768 CASCADE;
    DROP TABLE IF EXISTS memories_ollama CASCADE;
" 2>&1 | grep -v "does not exist" || true

log "Table dropped. Re-adding memories with new embeddings..."

# Re-add memories via mem0 API (this regenerates embeddings)
PROCESSED=0
FAILED=0

while IFS='|' read -r id content user_id; do
    PROCESSED=$((PROCESSED + 1))

    # Skip empty content
    if [ -z "${content}" ] || [ "${content}" = "null" ]; then
        log "[$PROCESSED/$TOTAL] Skipping memory ${id} (empty content)"
        continue
    fi

    # Show progress every 10 items
    if [ $((PROCESSED % 10)) -eq 0 ]; then
        log "[$PROCESSED/$TOTAL] Processing... (Failed: ${FAILED})"
    fi

    # Prepare JSON payload (no metadata - will be added by mem0)
    JSON_PAYLOAD=$(jq -n \
        --arg content "${content}" \
        --arg user_id "${user_id}" \
        '{
            messages: [{role: "user", content: $content}],
            user_id: $user_id
        }')

    # Add via API - retry up to 3 times on failure
    SUCCESS=false
    for attempt in 1 2 3; do
        RESPONSE=$(curl -sf -w "\n%{http_code}" -X POST "${MEM0_URL}/memories" \
            -H "Content-Type: application/json" \
            -d "${JSON_PAYLOAD}" 2>&1)

        HTTP_CODE=$(echo "$RESPONSE" | tail -1)
        BODY=$(echo "$RESPONSE" | head -n -1)

        if [ "$HTTP_CODE" = "200" ]; then
            SUCCESS=true
            break
        fi

        sleep 1
    done

    if [ "$SUCCESS" = false ]; then
        FAILED=$((FAILED + 1))
        log "[$PROCESSED/$TOTAL] FAILED: ${id} - User: ${user_id} (HTTP: $HTTP_CODE)"
        continue
    fi

done < "${TMP_DIR}/memories_export.txt"

log "Re-embedding complete!"
log "Processed: ${PROCESSED}"
log "Failed: ${FAILED}"
log "Success rate: $(( (PROCESSED - FAILED) * 100 / PROCESSED ))%"

# Verify new count
NEW_TOTAL=$(docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc \
    "SELECT COUNT(*) FROM memories;")

log "Original count: ${TOTAL}"
log "New count: ${NEW_TOTAL}"

if [ "${NEW_TOTAL}" -lt $((TOTAL - FAILED)) ]; then
    log "WARNING: New count is less than expected!"
    log "Backup available at: ${TMP_DIR}/pre_reembed_backup.sql.gz"
else
    log "✅ Re-embedding successful!"
    log "Cleaning up backup..."
    # Keep backup for 24 hours
    BACKUP_DIR="/Volumes/Data/backups/mem0/reembed"
    mkdir -p "${BACKUP_DIR}"
    cp "${TMP_DIR}/pre_reembed_backup.sql.gz" "${BACKUP_DIR}/pre_reembed_$(date +%Y%m%d_%H%M%S).sql.gz"
    log "Backup saved to: ${BACKUP_DIR}/"
fi
