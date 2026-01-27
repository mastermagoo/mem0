# mem0 Monitoring & Alerting

**Purpose:** Prevent data loss incidents by monitoring memory count and alerting on anomalies.

## Components

### 1. PostgreSQL Memory Exporter (`postgres_memory_exporter.py`)
- **Port:** 9094
- **Metrics Exposed:**
  - `mem0_memory_total` - Total memory count across all namespaces
  - `mem0_memory_count{namespace}` - Memory count per namespace
  - `mem0_memory_drop_percentage` - Percentage drop from previous scrape
  - `mem0_database_up` - Database connectivity status (1=up, 0=down)

### 2. Prometheus Configuration (`prometheus.yml`)
- Scrapes memory metrics every 30 seconds
- Stores time-series data for alerting and graphing

### 3. Grafana Alerts (`grafana_alerts.json`)
- **CRITICAL:** Memory count = 0 (fires after 2 minutes)
- **WARNING:** Memory count drops >50% (fires after 5 minutes)
- **CRITICAL:** PostgreSQL database unreachable (fires after 1 minute)
- **INFO:** Memory count below baseline of 1,968 (fires after 10 minutes)

## Setup Instructions

### Step 1: Deploy PostgreSQL Exporter

Add to `docker-compose.prd.yml`:

```yaml
  mem0_postgres_exporter:
    image: python:3.11-slim
    container_name: mem0_postgres_exporter
    networks:
      - mem0_internal_prd
    volumes:
      - ./monitoring/postgres_memory_exporter.py:/app/exporter.py:ro
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - EXPORTER_PORT=9094
    command: >
      sh -c "pip install -q psycopg &&
             python /app/exporter.py"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9094/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### Step 2: Update Prometheus

The `prometheus.yml` has been updated to scrape the new exporter on port 9094.

Restart Prometheus to pick up the new configuration:

```bash
docker restart <prometheus_container_name>
```

### Step 3: Configure Grafana Alerts

1. **Access Grafana:** http://localhost:3000 (or your Grafana URL)
2. **Add Prometheus Data Source:**
   - Navigate to: Configuration > Data Sources > Add data source
   - Type: Prometheus
   - URL: `http://prometheus:9090` (or appropriate URL)
   - Click "Save & Test"

3. **Import Alert Rules:**
   - Navigate to: Alerting > Alert Rules
   - Click "New Alert Rule"
   - Manually create alerts based on `grafana_alerts.json` configuration
   - OR use Grafana's JSON import if available

4. **Configure Telegram Notifications:**
   - Navigate to: Alerting > Notification channels > New channel
   - Type: Telegram
   - Bot API Token: `${TELEGRAM_BOT_TOKEN}` (from .env)
   - Chat ID: `${TELEGRAM_CHAT_ID}` (from .env)
   - Click "Test" to verify, then "Save"

5. **Link Alerts to Notification Channel:**
   - Edit each alert rule
   - Add Telegram notification channel
   - Save

### Step 4: Create Dashboard

Create a new dashboard with the following panels:

**Panel 1: Memory Count Over Time**
- Type: Graph
- Query: `mem0_memory_total`
- Alert threshold at 0 (red line)

**Panel 2: Memory Count by Namespace**
- Type: Graph
- Query: `mem0_memory_count`
- Legend: `{{namespace}}`

**Panel 3: Memory Drop Percentage**
- Type: Stat
- Query: `mem0_memory_drop_percentage * 100`
- Format: Percent
- Thresholds: 25% (yellow), 50% (red)

**Panel 4: Database Status**
- Type: Stat
- Query: `mem0_database_up`
- Value mappings: 0=DOWN (red), 1=UP (green)

## Testing Alerts

### Test 1: Database Down Alert
```bash
# Stop PostgreSQL
docker stop mem0_postgres_prd

# Wait 1 minute - should trigger "PostgreSQL Database Unreachable" alert
# Restore
docker start mem0_postgres_prd
```

### Test 2: Memory Count Zero Alert
**DO NOT TEST IN PRODUCTION** - This would require actual data loss.

Instead, verify the alert configuration is correct by checking:
```bash
# Query current memory count
curl -s http://localhost:9094/metrics | grep mem0_memory_total
# Should show: mem0_memory_total 1968
```

## Alert Response Procedures

### If "Memory Count is ZERO" fires:

1. **STOP IMMEDIATELY** - Do not restart containers
2. **Check backup status:**
   ```bash
   ls -lh /Volumes/Data/backups/mem0/daily/ | head -5
   ```
3. **Restore from latest backup:**
   ```bash
   cd /Volumes/Data/ai_projects/mem0-system
   ./scripts/restore_from_backup.sh <backup_date>
   ```
4. **Investigate root cause** - Check container logs, credential changes, embedding model changes
5. **Update incident documentation** in `docs/incidents/`

### If "Memory Count Dropped >50%" fires:

1. **Check if intentional** - Were memories deliberately deleted?
2. **Compare with backup:**
   ```bash
   # Current count
   docker exec mem0_postgres_prd psql -U mem0_user_prd -d mem0_prd -tAc "SELECT COUNT(*) FROM memories"

   # Backup count
   gunzip -c /Volumes/Data/backups/mem0/daily/<latest>/postgres/*.sql.gz | grep -c "^COPY"
   ```
3. **If unexpected drop, restore from backup**
4. **Check for:**
   - Container recreations (`docker ps -a | grep mem0`)
   - Credential changes (`.env` file modifications)
   - Embedding model changes (Ollama vs OpenAI)

### If "PostgreSQL Database Unreachable" fires:

1. **Check container status:**
   ```bash
   docker ps --filter "name=postgres"
   ```
2. **Check logs:**
   ```bash
   docker logs mem0_postgres_prd --tail 50
   ```
3. **Restart if needed:**
   ```bash
   docker restart mem0_postgres_prd
   ```
4. **Verify connectivity:**
   ```bash
   docker exec mem0_postgres_prd pg_isready -U mem0_user_prd
   ```

## Maintenance

### Check Exporter Status
```bash
# Test metrics endpoint
curl -s http://localhost:9094/metrics | head -20

# Check exporter logs (if deployed as container)
docker logs <exporter_container_name>
```

### Update Alert Thresholds

Edit `grafana_alerts.json` and reimport into Grafana if thresholds need adjustment.

### Monitor Alert History

Navigate to: Grafana > Alerting > Alert Rules > History

## References

- **Incident:** `/Volumes/Data/ai_projects/mem0-system/docs/incidents/2026-01-27_DATA_LOSS_RESTORATION.md`
- **CLAUDE.md:** Rules and incident learnings
- **Prometheus Docs:** https://prometheus.io/docs/
- **Grafana Alerting Docs:** https://grafana.com/docs/grafana/latest/alerting/
