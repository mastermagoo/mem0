# TEST Environment Status

**Date:** 2026-01-10 16:30  
**Status:** ✅ RUNNING

---

## 🎯 Current Status

**TEST environment is now running.**

**Reason it wasn't running:**
- TEST environment doesn't have auto-start configured (unlike PRD)
- TEST must be started manually with: `docker compose -f docker-compose.test.yml up -d`

---

## 📊 Running Containers

| Container | Status | Image |
|-----------|--------|-------|
| mem0_postgres_test | ✅ Healthy | pgvector/pgvector:pg17 |
| mem0_neo4j_test | ✅ Healthy | neo4j:5.13.0 |
| mem0_server_test | ✅ Healthy | mem0-fixed:local |
| mem0_grafana_test | ✅ Healthy | grafana/grafana:latest |
| mem0_telegram_bot_test | ✅ Running | mem0-system-telegram_bot |

---

## 🚀 Starting TEST Environment

**Manual Start:**
```bash
cd /Volumes/Data/ai_projects/mem0-system
docker compose -f docker-compose.test.yml up -d
```

**Stop:**
```bash
cd /Volumes/Data/ai_projects/mem0-system
docker compose -f docker-compose.test.yml down
```

**Status Check:**
```bash
docker compose -f docker-compose.test.yml ps
```

---

## ⚙️ Configuration

**Ports:**
- mem0 API: `http://localhost:18888` (TEST)
- mem0 API: `http://localhost:8889` (PRD)
- PostgreSQL: `localhost:15432` (TEST) vs `localhost:5433` (PRD)
- Neo4j HTTP: `localhost:17474` (TEST) vs `localhost:7475` (PRD)
- Neo4j Bolt: `localhost:17687` (TEST) vs `localhost:7688` (PRD)
- Grafana: `localhost:13000` (TEST) vs `localhost:3001` (PRD)

**Environment File:**
- TEST uses: `.env.test` (if exists) or `.env` with `DEPLOYMENT_ENV=test`

**Data Storage:**
- TEST: `${MEM0_DATA_ROOT:-/Users/kermit/mem0-data-test}/`
- PRD: `${MEM0_DATA_ROOT:-/Volumes/NAS/mem0-prd}/`

---

## 🔄 Auto-Start (Optional)

**TEST doesn't have auto-start configured** (unlike PRD which has `com.mem0.prd.plist`).

**If you want TEST to auto-start on boot:**

1. Create `com.mem0.test.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mem0.test</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/docker</string>
        <string>compose</string>
        <string>-f</string>
        <string>/Volumes/Data/ai_projects/mem0-system/docker-compose.test.yml</string>
        <string>up</string>
        <string>-d</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Volumes/Data/ai_projects/mem0-system</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
    
    <key>StandardOutPath</key>
    <string>/tmp/mem0_test_launchd.log</string>
    
    <key>StandardErrorPath</key>
    <string>/tmp/mem0_test_launchd_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

2. Install:
```bash
cp com.mem0.test.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.mem0.test.plist
```

---

## ✅ Verification

**Check all TEST containers:**
```bash
docker ps --filter "name=mem0.*test"
```

**Test API:**
```bash
curl http://localhost:18888/docs
```

**Check logs:**
```bash
docker logs mem0_server_test --tail 20
```

---

**Status:** ✅ TEST environment is running and operational!
