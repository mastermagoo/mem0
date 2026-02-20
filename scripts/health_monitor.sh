#!/bin/bash
# mem0 Health Monitor - Self-contained in mem0-system repo
# Monitors mem0 PRD and sends Telegram alerts on failures

# Fix PATH for cron environment (include Homebrew for curl)
export PATH="/opt/homebrew/bin:/Users/kermit/.orbstack/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Use 127.0.0.1 instead of localhost for cron compatibility
MEM0_URL="${MEM0_URL:-http://127.0.0.1:8889}"
MEM0_REPO_DIR="${MEM0_REPO_DIR:-/Volumes/Data/ai_projects/mem0-system}"
LOG_FILE="${MEM0_LOG_FILE:-/tmp/mem0_health.log}"
STATE_DIR="${MEM0_REPO_DIR}/.health_state"
mkdir -p "$STATE_DIR"

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
  local state_file="${STATE_DIR}/$(echo "$message" | md5)"

  # Only send if not alerted in last 60 minutes
  if [[ -f "$state_file" ]]; then
    local last_alert=$(cat "$state_file")
    local now=$(date +%s)
    local diff=$((now - last_alert))
    if [[ $diff -lt 3600 ]]; then
      log "Skipping duplicate alert (last sent ${diff}s ago): $message"
      return
    fi
  fi

  if [[ -n "$TELEGRAM_BOT_TOKEN" ]] && [[ -n "$TELEGRAM_CHAT_ID" ]]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${TELEGRAM_CHAT_ID}" \
      -d "text=🚨 mem0 PRD ALERT: ${message}" \
      -d "parse_mode=Markdown" > /dev/null 2>&1
    echo $(date +%s) > "$state_file"
  else
    log "WARNING: Telegram not configured, cannot send alert"
  fi
}

check_api() {
  # Check /health endpoint for reliable status check
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${MEM0_URL}/health" 2>/dev/null)
  if [[ "$http_code" == "200" ]]; then
    return 0
  else
    log "API health check failed: HTTP $http_code"
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
  # Clear alert state when healthy
  rm -f "${STATE_DIR}"/* 2>/dev/null
fi
