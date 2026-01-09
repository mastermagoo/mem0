#!/bin/bash
# mem0 Health Monitor - Self-contained in mem0-system repo
# Monitors mem0 PRD and sends Telegram alerts on failures

MEM0_URL="${MEM0_URL:-http://localhost:8889}"
MEM0_REPO_DIR="${MEM0_REPO_DIR:-/Volumes/Data/ai_projects/mem0-system}"
LOG_FILE="${MEM0_LOG_FILE:-/tmp/mem0_health.log}"

# Telegram config (from env or .env file)
if [[ -f "${MEM0_REPO_DIR}/.env" ]]; then
  source "${MEM0_REPO_DIR}/.env"
fi

TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

SERVICES=("mem0_server_prd" "mem0_neo4j_prd" "mem0_postgres_prd")

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_telegram_alert() {
  local message="$1"
  if [[ -n "$TELEGRAM_BOT_TOKEN" ]] && [[ -n "$TELEGRAM_CHAT_ID" ]]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${TELEGRAM_CHAT_ID}" \
      -d "text=🚨 mem0 PRD ALERT: ${message}" \
      -d "parse_mode=Markdown" > /dev/null 2>&1
  else
    log "WARNING: Telegram not configured, cannot send alert"
  fi
}

check_api() {
  response=$(curl -s --max-time 10 "${MEM0_URL}/docs" 2>/dev/null)
  if echo "$response" | grep -q "html"; then
    return 0
  else
    return 1
  fi
}

check_container() {
  local service="$1"
  if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
    return 0
  else
    return 1
  fi
}

# Main health check
all_healthy=true

for service in "${SERVICES[@]}"; do
  if ! check_container "$service"; then
    log "❌ $service is NOT running"
    send_telegram_alert "$service is DOWN"
    all_healthy=false
  fi
done

if ! check_api; then
  log "❌ mem0 API not responding at ${MEM0_URL}"
  send_telegram_alert "mem0 API not responding at ${MEM0_URL}"
  all_healthy=false
fi

if $all_healthy; then
  log "✅ All mem0 services healthy"
fi
