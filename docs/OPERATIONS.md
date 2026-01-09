# Mem0 Personal AI Memory - Operations Guide

**Last Updated:** 2025-10-16
**Version:** 1.0
**System:** mem0 persistent memory on Mac Studio M1 Max

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Backup Procedures](#backup-procedures)
3. [Restore Procedures](#restore-procedures)
4. [Monitoring](#monitoring)
5. [Health Checks](#health-checks)
6. [Alerting](#alerting)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)
9. [Security](#security)

---

## System Overview

### Architecture

The mem0 system consists of the following components:

- **mem0_server** - FastAPI-based memory server (port 8888)
- **mem0_postgres** - PostgreSQL database with pgvector (port 5433)
- **mem0_neo4j** - Neo4j graph database (ports 7474, 7687)
- **mem0_grafana** - Grafana visualization (port 3001)
- **mem0_telegram_bot** - Telegram notification bot

### Data Locations

- **PostgreSQL Data:** `/Users/kermit/mem0-data/postgres`
- **Neo4j Data:** `/Users/kermit/mem0-data/neo4j`
- **Application Data:** `/Users/kermit/mem0-data/data`
- **Grafana Data:** `/Users/kermit/mem0-data/grafana`
- **Backups:** `/Volumes/Data/backups/mem0/` (Updated: 2025-11-04)
  - Daily backups: `/Volumes/Data/backups/mem0/daily/` (retention: 7 days)
  - Weekly backups: `/Volumes/Data/backups/mem0/weekly/` (retention: 4 weeks)
  - Monthly backups: `/Volumes/Data/backups/mem0/monthly/` (retention: 12 months)
  - Hourly backups: `/Volumes/Data/backups/mem0/hourly/` (retention: 24 hours, via SSD backup system)

### Network

- **Internal Network:** `mem0_internal` (bridge)
- **External Network:** `intel-network` (shared with intel-system)

---

## Backup Procedures

### Automated Backups

Automated backups run daily at 2:30 AM via cron. The backup script is located at:

```
/Volumes/Data/ai_projects/intel-system/deployment/scripts/backup_mem0.sh
```

**Additional Hourly Backups**: mem0 data is also backed up hourly via the unified SSD backup system (`scripts/backup_system_automated.sh`).

#### Backup Types

1. **Daily Backups** - Every day, retained for 7 days
2. **Weekly Backups** - Every Sunday, retained for 4 weeks
3. **Monthly Backups** - 1st of each month, retained for 12 months

#### What Gets Backed Up

- PostgreSQL database (compressed SQL dump)
- Neo4j database (filesystem backup)
- Verification checksums
- Metadata and timestamps

### Manual Backup

To perform a manual backup:

```bash
cd /Volumes/Data/ai_projects/intel-system/deployment/scripts
./backup_mem0.sh
```

**Or use the unified backup coordinator:**

```bash
cd /Volumes/Data/ai_projects/intel-system
bash scripts/backup_coordinator.sh daily
```

#### Check Backup Status

View backup logs:

```bash
tail -f /tmp/mem0_backup.log
tail -f /tmp/mem0_backup_cron.log  # Cron job logs
```

List available backups:

```bash
ls -lh /Volumes/Data/backups/mem0/daily/
ls -lh /Volumes/Data/backups/mem0/weekly/
ls -lh /Volumes/Data/backups/mem0/monthly/
ls -lh /Volumes/Data/backups/mem0/hourly/  # Hourly backups (via SSD backup system)
```

#### Backup Configuration

Edit the backup script to modify settings:

```bash
# In backup_mem0.sh
DAILY_RETENTION=7    # Keep 7 daily backups
WEEKLY_RETENTION=4   # Keep 4 weekly backups
MONTHLY_RETENTION=12 # Keep 12 monthly backups
```

### Setting Up Cron

Add to crontab to run daily at 2:30 AM (already configured):

```bash
crontab -e
```

Current cron entry:
```
30 2 * * * /Volumes/Data/ai_projects/intel-system/deployment/scripts/backup_mem0.sh >> /tmp/mem0_backup_cron.log 2>&1
```

Verify cron job:

```bash
crontab -l | grep backup_mem0
```

---

## Restore Procedures

### PostgreSQL Restore

1. **Stop mem0_server** (to prevent writes during restore):

```bash
docker stop mem0_server
```

2. **List available backups:**

```bash
ls -lh /Volumes/intel-system/backups/mem0/daily/
```

3. **Restore from backup:**

```bash
# Choose a backup timestamp (e.g., 20251104_023000)
BACKUP_TIMESTAMP="20251104_023000"

# Restore PostgreSQL
gunzip < /Volumes/Data/backups/mem0/daily/${BACKUP_TIMESTAMP}/postgres/mem0_${BACKUP_TIMESTAMP}.sql.gz | \
    docker exec -i mem0_postgres_prd psql -U mem0_user_prd -d mem0_prd
```

4. **Verify restore:**

```bash
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "SELECT COUNT(*) FROM memories;"
```

5. **Restart mem0_server:**

```bash
docker start mem0_server
```

### Neo4j Restore

1. **Stop mem0_neo4j:**

```bash
docker stop mem0_neo4j
```

2. **Restore from backup:**

```bash
# Choose a backup timestamp
BACKUP_TIMESTAMP="20251016_020000"

# Remove existing data
rm -rf /Users/kermit/mem0-data/neo4j/*

# Extract backup
tar -xzf /Volumes/intel-system/backups/mem0/daily/${BACKUP_TIMESTAMP}/neo4j/mem0_neo4j_${BACKUP_TIMESTAMP}.tar.gz \
    -C /Users/kermit/mem0-data/
```

3. **Restart Neo4j:**

```bash
docker start mem0_neo4j
```

4. **Verify Neo4j:**

```bash
curl http://127.0.0.1:7474
```

### Full System Restore

For disaster recovery:

```bash
# Stop all services
cd /Volumes/intel-system/deployment/docker/mem0_tailscale
docker-compose down

# Restore PostgreSQL
gunzip < /Volumes/intel-system/backups/mem0/monthly/TIMESTAMP/postgres/*.sql.gz | \
    docker exec -i mem0_postgres psql -U mem0_user -d mem0

# Restore Neo4j
rm -rf /Users/kermit/mem0-data/neo4j/*
tar -xzf /Volumes/intel-system/backups/mem0/monthly/TIMESTAMP/neo4j/*.tar.gz \
    -C /Users/kermit/mem0-data/

# Restart all services
docker-compose up -d

# Verify health
/Volumes/intel-system/deployment/scripts/check_mem0_health.sh
```

---

## DR Runbook (Wingman-gated approvals)

Updating existing guide instead of creating new version

### Required approvals (Wingman)

- **Gate A — Pre-DR readiness**: Wingman confirms current PRD state snapshot + rollback readiness
- **Gate B — Pre-teardown**: Wingman approves stopping/removing PRD containers
- **Gate C — Post-cold-start validation**: Wingman confirms API/DB/Neo4j/Grafana checks pass
- **Gate D — Telegram E2E**: Wingman confirms Telegram bots respond in both TEST and PRD

### Telegram validation requirements

- **Wingman Telegram (TEST/PRD)**: confirm bot can reach Wingman API `/health` from its container network and is polling (logs show “authorized” and no crash loops).
- **mem0 Telegram (TEST/PRD)**: run with compose profile `telegram` and confirm `/start`, `/remember`, and `/recall` succeed end-to-end.


## Monitoring

### Prometheus Metrics

Mem0 metrics are exported to Prometheus on port 9103.

#### Starting the Metrics Exporter

**Option 1: Python (foreground)**

```bash
cd /Volumes/intel-system/deployment/scripts
python3 mem0_metrics_exporter.py
```

**Option 2: launchd (background, auto-start)**

```bash
# Copy plist to LaunchAgents
cp /Volumes/intel-system/deployment/scripts/com.mem0.metrics.plist \
    ~/Library/LaunchAgents/

# Load the service
launchctl load ~/Library/LaunchAgents/com.mem0.metrics.plist

# Check status
launchctl list | grep mem0

# View logs
tail -f /var/log/mem0_metrics.log
```

**Option 3: Docker (recommended)**

Create a Docker container for the metrics exporter:

```bash
docker run -d \
    --name mem0_metrics_exporter \
    --network mem0_internal \
    -p 9103:9103 \
    -e POSTGRES_HOST=mem0_postgres \
    -e POSTGRES_PORT=5432 \
    -e POSTGRES_USER=mem0_user \
    -e POSTGRES_PASSWORD=your_password \
    -e MEM0_URL=http://mem0_server:8888 \
    --restart unless-stopped \
    python:3.12-slim \
    python /app/mem0_metrics_exporter.py
```

#### Available Metrics

- `mem0_service_up` - Service availability (1=up, 0=down)
- `mem0_postgres_up` - PostgreSQL availability
- `mem0_api_response_time_seconds` - API response time histogram
- `mem0_api_requests_total` - Total API requests
- `mem0_api_errors_total` - Total API errors
- `mem0_memories_total` - Total memories stored
- `mem0_users_total` - Total users
- `mem0_database_size_bytes` - Database size
- `mem0_database_connections` - Active connections
- `mem0_query_duration_seconds` - Query duration histogram

#### Adding to Prometheus

Add this to your Prometheus configuration (`prometheus.yml`):

```yaml
scrape_configs:
  - job_name: 'mem0-metrics'
    static_configs:
      - targets: ['host.docker.internal:9103']
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: '/metrics'
```

Reload Prometheus:

```bash
docker exec intel-prometheus-standalone killall -HUP prometheus
```

Verify metrics are being scraped:

```bash
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="mem0-metrics")'
```

### Grafana Dashboard

#### Importing the Dashboard

1. Access Grafana at http://localhost:3001 (or your Grafana port)
2. Login with credentials (`GRAFANA_USER` / `GRAFANA_PASSWORD` from your `.env`)
3. Navigate to **Dashboards** → **Import**
4. Upload `/Volumes/intel-system/deployment/scripts/mem0_grafana_dashboard.json`
5. Select your Prometheus datasource
6. Click **Import**

#### Dashboard Panels

The dashboard includes:

- **Service Health Overview** - Uptime status
- **Total Memories Stored** - Memory count over time
- **Active Users** - User count
- **API Response Time** - p50, p95, p99 percentiles
- **Database Query Duration** - Query performance
- **Database Size** - Storage growth
- **Active Database Connections** - Connection pool usage
- **API Request Rate** - Requests per second
- **API Error Rate** - Errors per second (with alerts)
- **Memory Growth** - 7-day trend

#### Dashboard URL

After import, the dashboard will be available at:

```
http://localhost:3001/d/mem0-dashboard/personal-ai-memory-mem0
```

---

## Health Checks

### Manual Health Check

Run the health check script:

```bash
/Volumes/intel-system/deployment/scripts/check_mem0_health.sh
```

#### What It Checks

1. **mem0_server** - Container health and API endpoint
2. **PostgreSQL** - Container health and database connectivity
3. **Neo4j** - Container health and HTTP endpoint
4. **Disk Space** - Available storage (threshold: 10GB)
5. **Grafana** - Container health and web interface

### Automated Health Checks

Set up cron to run health checks every 5 minutes:

```bash
crontab -e
```

Add:

```
*/5 * * * * /Volumes/intel-system/deployment/scripts/check_mem0_health.sh >> /tmp/mem0_health_cron.log 2>&1
```

### Health Check Logs

View health check logs:

```bash
tail -f /tmp/mem0_health.log
```

### Health Status Files

Alert cooldown state is stored in:

```
/var/tmp/mem0_health/alert_*.last
```

Clear cooldown to force immediate alerts:

```bash
rm /var/tmp/mem0_health/alert_*.last
```

---

## Alerting

### Telegram Alerts

Alerts are sent via Telegram when issues are detected.

#### Alert Types

- `mem0_server_down` - mem0_server container not running
- `mem0_server_endpoint` - API endpoint not responding
- `postgresql_down` - PostgreSQL container not running
- `postgresql_connection` - Cannot connect to PostgreSQL
- `postgresql_db_access` - Cannot access mem0 database
- `neo4j_down` - Neo4j container not running
- `neo4j_endpoint` - Neo4j HTTP endpoint not responding
- `disk_space_low` - Available disk space < 10GB
- `backup_success` - Backup completed successfully
- `backup_failed` - Backup failed

#### Testing Alerts

Send a test alert:

```bash
/Volumes/intel-system/deployment/scripts/alert_mem0.sh \
    "test_alert" \
    "This is a test alert from mem0 system" \
    "INFO"
```

#### Alert Configuration

Telegram credentials are loaded from:

```
/Volumes/intel-system/deployment/docker/mem0_tailscale/.env
```

Required variables:

```bash
TELEGRAM_BOT_TOKEN="your_bot_token"
TELEGRAM_CHAT_ID="your_chat_id"
```

#### Alert Cooldown

To prevent alert spam, each alert type has a 1-hour cooldown. Modify in `check_mem0_health.sh`:

```bash
ALERT_COOLDOWN=3600  # 1 hour in seconds
```

---

## Troubleshooting

### mem0_server Not Starting

**Check logs:**

```bash
docker logs mem0_server --tail 50
```

**Common issues:**

1. **Invalid OpenAI API Key**
   - Update key in `.env` file
   - Restart container: `docker restart mem0_server`

2. **PostgreSQL not ready**
   - Check PostgreSQL health: `docker exec mem0_postgres pg_isready -U mem0_user`
   - Wait for health check to pass

3. **Port already in use**
   - Check port: `lsof -i :8888`
   - Change port in `.env` and docker-compose.yml

### PostgreSQL Connection Issues

**Test connection:**

```bash
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "SELECT 1;"
```

**Check container health:**

```bash
docker inspect mem0_postgres --format='{{.State.Health.Status}}'
```

**View PostgreSQL logs:**

```bash
docker logs mem0_postgres --tail 50
```

### Neo4j Connection Issues

**Test Neo4j:**

```bash
curl http://127.0.0.1:7474
```

**Check Neo4j logs:**

```bash
docker logs mem0_neo4j --tail 50
```

**Access Neo4j Browser:**

Open http://localhost:7474 in browser.

### Disk Space Full

**Check disk usage:**

```bash
df -h /Volumes/intel-system
du -sh /Users/kermit/mem0-data/*
```

**Clean up old backups:**

```bash
# Remove backups older than retention policy
cd /Volumes/intel-system/backups/mem0
find daily/ -type d -mtime +7 -exec rm -rf {} \;
find weekly/ -type d -mtime +28 -exec rm -rf {} \;
find monthly/ -type d -mtime +365 -exec rm -rf {} \;
```

**Clean Docker:**

```bash
docker system prune -a --volumes
```

### Metrics Not Appearing in Prometheus

**Check metrics exporter:**

```bash
# Is it running?
ps aux | grep mem0_metrics_exporter

# Test metrics endpoint
curl http://localhost:9103/metrics
```

**Check Prometheus targets:**

```bash
# Via API
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job=="mem0-metrics")'

# Via UI
open http://localhost:9090/targets
```

**Restart metrics exporter:**

```bash
# If using launchd
launchctl unload ~/Library/LaunchAgents/com.mem0.metrics.plist
launchctl load ~/Library/LaunchAgents/com.mem0.metrics.plist
```

### Grafana Dashboard Not Loading

**Check Grafana:**

```bash
docker logs mem0_grafana --tail 50
```

**Access Grafana:**

```
http://localhost:3001
```

**Re-import dashboard:**

Delete old dashboard and re-import from JSON file.

---

## Maintenance

### Regular Maintenance Tasks

#### Daily

- [x] Automated backup runs at 2 AM
- [x] Health checks run every 5 minutes
- [x] Prometheus scrapes metrics every 15 seconds

#### Weekly

- [ ] Review backup logs for failures
- [ ] Check disk space usage trends
- [ ] Review Grafana dashboards for anomalies

#### Monthly

- [ ] Test restore procedure with monthly backup
- [ ] Review and update alert thresholds
- [ ] Clean up old logs

### Database Maintenance

#### PostgreSQL Vacuum

```bash
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "VACUUM ANALYZE;"
```

#### Check Database Size

```bash
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "
    SELECT pg_size_pretty(pg_database_size('mem0')) AS db_size;
"
```

#### Analyze Table Statistics

```bash
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "
    SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
    FROM pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Log Rotation

Logs are stored in `/tmp` and should be rotated:

```bash
# Truncate logs older than 7 days
find /tmp -name "mem0_*.log" -mtime +7 -exec truncate -s 0 {} \;
```

### Container Updates

Update mem0 containers:

```bash
cd /Volumes/intel-system/deployment/docker/mem0_tailscale

# Pull latest images
docker-compose pull

# Restart with new images
docker-compose down
docker-compose up -d

# Verify health
/Volumes/intel-system/deployment/scripts/check_mem0_health.sh
```

---

## Security

### Credentials

All credentials are stored in:

```
/Volumes/intel-system/deployment/docker/mem0_tailscale/.env
```

**Never commit this file to git!**

### Backup Security

Backups contain sensitive data. Ensure:

- Backups are stored on encrypted volumes
- Access is restricted to authorized users
- Backups are regularly tested

### Network Security

- mem0_server is only accessible via localhost (127.0.0.1)
- External access is via Tailscale VPN
- PostgreSQL and Neo4j are not exposed externally

### API Keys

Rotate API keys regularly:

```bash
# Edit .env file
nano /Volumes/intel-system/deployment/docker/mem0_tailscale/.env

# Update OPENAI_API_KEY
# Update MEM0_API_KEY (if needed)

# Restart services
docker-compose restart
```

---

## Quick Reference

### Common Commands

```bash
# Health check
/Volumes/intel-system/deployment/scripts/check_mem0_health.sh

# Manual backup
/Volumes/intel-system/deployment/scripts/backup_mem0.sh

# Send test alert
/Volumes/intel-system/deployment/scripts/alert_mem0.sh "test" "Test message" "INFO"

# View logs
docker logs -f mem0_server
docker logs -f mem0_postgres
docker logs -f mem0_neo4j

# Check metrics
curl http://localhost:9103/metrics

# Restart services
docker-compose restart
```

### Important Paths

- Scripts: `/Volumes/intel-system/deployment/scripts/`
- Docker Compose: `/Volumes/intel-system/deployment/docker/mem0_tailscale/`
- Data: `/Users/kermit/mem0-data/`
- Backups: `/Volumes/intel-system/backups/mem0/`
- Logs: `/tmp/mem0_*.log`

### Useful Queries

**PostgreSQL - Count memories:**

```bash
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "SELECT COUNT(*) FROM memories;"
```

**PostgreSQL - Database size:**

```bash
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "SELECT pg_size_pretty(pg_database_size('mem0'));"
```

**Check all container health:**

```bash
docker ps --filter "name=mem0" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## Support

For issues or questions:

1. Check logs: `docker logs mem0_server`
2. Run health check: `./check_mem0_health.sh`
3. Review Grafana dashboards
4. Check Prometheus metrics

**Created:** 2025-10-16
**Author:** Worker 5 - DevOps Engineer
**Version:** 1.0
