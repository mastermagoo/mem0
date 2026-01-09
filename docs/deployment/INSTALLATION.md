# mem0-system Installation & Setup

**Last Updated:** 2026-01-09
**Version:** 2.0 (Standalone)

## 🎯 Overview

This repo contains a **standalone** mem0 deployment. All dependencies, scripts, and configurations are self-contained within this repository.

**✅ No external dependencies on intel-system or any other repo**

---

## 📋 Prerequisites

1. Docker & Docker Compose installed
2. Mac Studio M1 Max (or compatible)
3. Ollama running on host at `http://localhost:11434`
4. Models pulled: `mistral:7b-instruct-q5_K_M`, `nomic-embed-text:latest`

---

## 🚀 Quick Start

### 1. Build Docker Image

```bash
cd /Volumes/Data/ai_projects/mem0-system

# Build the image
docker build -f Dockerfile.mem0 -t mem0-fixed:local .
```

### 2. Configure Environment

```bash
# Copy example env file
cp env.example .env

# Edit .env and set:
# - DEPLOYMENT_ENV=prd
# - POSTGRES_PASSWORD=your_secure_password
# - NEO4J_PASSWORD=your_secure_password
# - MEM0_API_KEY=your_api_key
# - GRAFANA_PASSWORD=your_password
# - TELEGRAM_BOT_TOKEN=your_token (optional)
```

### 3. Deploy Production

```bash
./deploy_prd.sh up
```

### 4. Verify Deployment

```bash
./deploy_prd.sh validate

# Check API
curl http://localhost:8888/docs
```

---

## 🔧 Post-Installation Setup

### Install Auto-Start Service (launchd)

```bash
# Copy plist to LaunchAgents
cp com.mem0.prd.plist ~/Library/LaunchAgents/

# Load the service
launchctl load ~/Library/LaunchAgents/com.mem0.prd.plist

# Verify
launchctl list | grep mem0
```

### Configure Automated Backups

```bash
# Edit crontab
crontab -e

# Add backup job (daily at 2:30 AM):
30 2 * * * /Volumes/Data/ai_projects/mem0-system/scripts/backup_mem0.sh daily >> /tmp/mem0_backup.log 2>&1

# Add weekly backup (Sundays at 3:00 AM):
0 3 * * 0 /Volumes/Data/ai_projects/mem0-system/scripts/backup_mem0.sh weekly >> /tmp/mem0_backup.log 2>&1
```

### Configure Health Monitoring

```bash
# Add health check (every 5 minutes):
*/5 * * * * /Volumes/Data/ai_projects/mem0-system/scripts/health_monitor.sh >> /tmp/mem0_health.log 2>&1
```

---

## 📁 Directory Structure

```
mem0-system/
├── docker-compose.prd.yml    # Production compose file
├── docker-compose.test.yml   # Test compose file  
├── docker-compose.yml         # Generic/dev compose file
├── Dockerfile.mem0            # Main mem0 image
├── deploy_prd.sh              # Production deployment script
├── .env                       # Environment config (DO NOT COMMIT)
├── env.example                # Environment template
├── com.mem0.prd.plist         # launchd auto-start config
├── scripts/
│   ├── backup_mem0.sh         # Backup script
│   └── health_monitor.sh      # Health monitoring
├── monitoring/
│   └── prometheus.yml         # Prometheus config
├── telegram_bot/              # Telegram bot (optional)
└── docs/                      # Documentation
```

---

## 🔒 Security Notes

- ✅ No hardcoded credentials in any files
- ✅ All secrets in `.env` file (git-ignored)
- ✅ Docker labels use `com.mem0-system` (not intel-system)
- ✅ All paths are self-contained within this repo

---

## 🔄 Upgrade from Old Deployment

If migrating from old intel-system/mem0-system location:

1. Stop old deployment
2. Backup data: `docker exec mem0_postgres_prd pg_dump ...`
3. Build new image
4. Deploy with new compose files
5. Restore data if needed
6. Update cron jobs to new paths
7. Remove old intel-system/mem0-system directory

See `CLEANUP_INTEL_SYSTEM.md` for detailed cleanup steps.

---

## 📞 Support

- Health logs: `/tmp/mem0_health.log`
- Backup logs: `/tmp/mem0_backup.log`
- Deployment logs: `docker compose logs`

---

## ✅ Verification Checklist

After installation:

- [ ] Docker image `mem0-fixed:local` built
- [ ] PRD containers running (5 services)
- [ ] API accessible at `http://localhost:8888/docs`
- [ ] launchd service loaded
- [ ] Cron jobs configured
- [ ] Test backup runs successfully
- [ ] Health monitor runs successfully
- [ ] Telegram alerts working (if configured)
- [ ] Zero references to intel-system in docker ps/logs
