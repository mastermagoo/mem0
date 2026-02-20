# Auto-Start Setup for mem0 Environments

**Date:** 2026-01-10  
**Status:** ✅ Configured

---

## 🚀 Auto-Start Services

Both PRD and TEST environments have launchd services configured for automatic startup on boot.

---

## ✅ PRD Auto-Start

**Service:** `com.mem0.prd`  
**File:** `~/Library/LaunchAgents/com.mem0.prd.plist`  
**Script:** `/Volumes/Data/ai_projects/mem0-system/deploy_prd.sh up`

**Status:** ✅ Installed and configured

**To load:**
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mem0.prd.plist
```

**To unload:**
```bash
launchctl bootout gui/$(id -u)/com.mem0.prd
```

**To check status:**
```bash
launchctl list | grep mem0
```

---

## ✅ TEST Auto-Start

**Service:** `com.mem0.test`  
**File:** `~/Library/LaunchAgents/com.mem0.test.plist`  
**Script:** `/Volumes/Data/ai_projects/mem0-system/scripts/start_test.sh`

**Status:** ✅ Installed and configured

**To load:**
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mem0.test.plist
```

**To unload:**
```bash
launchctl bootout gui/$(id -u)/com.mem0.test
```

**To check status:**
```bash
launchctl list | grep mem0
```

---

## 📋 Cron Jobs

### Health Monitor
**Schedule:** Every 5 minutes (`*/5 * * * *`)  
**Script:** `/Volumes/Data/ai_projects/mem0-system/scripts/health_monitor.sh`  
**Log:** `/tmp/mem0_health_cron.log`

**Status:** ✅ Scheduled

**To verify:**
```bash
crontab -l | grep health_monitor
```

### Backup
**Schedule:** 
- Daily: `30 2 * * *` (2:30 AM)
- Weekly: `0 3 * * 0` (3:00 AM Sunday)

**Script:** `/Volumes/Data/ai_projects/mem0-system/scripts/backup_mem0.sh`  
**Log:** `/tmp/mem0_backup_cron.log`

**Status:** ✅ Scheduled

**To verify:**
```bash
crontab -l | grep backup_mem0
```

---

## 🔍 Verification

**Check all services:**
```bash
# Launchd services
ls -la ~/Library/LaunchAgents/com.mem0.*.plist

# Cron jobs
crontab -l | grep mem0

# Service logs
tail -f /tmp/mem0_prd_launchd.log
tail -f /tmp/mem0_test_launchd.log
tail -f /tmp/mem0_health_cron.log
tail -f /tmp/mem0_backup_cron.log
```

---

## ⚠️ Notes

**macOS Launchd:**
- On newer macOS versions, use `launchctl bootstrap` instead of `launchctl load`
- Services run in user context (gui/$(id -u))
- Services start automatically on login/boot

**Cron Jobs:**
- Run as the current user
- Logs are in `/tmp/`
- Check logs regularly for errors

---

**Status:** ✅ All auto-start services and cron jobs configured!
