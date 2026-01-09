# Intel-System Cleanup - Remove mem0/wingman Artifacts

**Date:** 2026-01-09
**Purpose:** Complete separation of mem0-system and wingman-system from intel-system

## ⚠️ CRITICAL - Items to Remove from intel-system

### 1. Old mem0-system Directory
```bash
# REMOVE THIS ENTIRE DIRECTORY:
/Volumes/Data/ai_projects/intel-system/mem0-system/
```

### 2. Update Monitoring Scripts

**File:** `/Volumes/Data/ai_projects/intel-system/shared-services/backups/backup_mem0.sh`
- ✅ Already updated to point to new location

**File:** `/Volumes/Data/ai_projects/intel-system/docs/.../mem0/monitoring/mem0_health_monitor.sh`
- ✅ Already updated to point to new location

### 3. Update Cron Jobs

```bash
# Edit crontab:
crontab -e

# UPDATE these lines to use new paths:
# Old: /Volumes/Data/ai_projects/intel-system/shared-services/backups/backup_mem0.sh
# New: /Volumes/Data/ai_projects/mem0-system/scripts/backup_mem0.sh

# Old: .../intel-system/docs/.../mem0/monitoring/mem0_health_monitor.sh
# New: /Volumes/Data/ai_projects/mem0-system/scripts/health_monitor.sh
```

### 4. Check for References in Documentation

Files with intel-system references (already in archive, OK to keep):
- docs/archive/*.md (historical documentation)

### 5. SAP-Specific mem0 Scripts

**Location:** `/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP/docs/00-strategic/mem0/`

**Action:** Review these scripts - they may be SAP-specific intelligence workflows
that use mem0 but are not part of core mem0-system. If they're SAP-specific,
they can stay in intel-system.

## ✅ Items That Are Correct

1. **Namespace name "intel_system"** - This is a mem0 namespace name (data partition),
   not a path reference. It's correct and should remain.

2. **Monitoring scripts already updated** - backup_mem0.sh and health_monitor already
   point to `/Volumes/Data/ai_projects/mem0-system/`

3. **Labels in docker-compose** - Changed from `com.intel-system` to `com.mem0-system`

## 📋 Verification Checklist

- [ ] Remove `/Volumes/Data/ai_projects/intel-system/mem0-system/` directory
- [ ] Update cron jobs to use new script paths
- [ ] Test backup script from new location
- [ ] Test health monitor from new location
- [ ] Verify no references to mem0-system in intel-system docker-compose files
- [ ] Verify no references to wingman-system in intel-system docker-compose files

## 🔍 Verification Commands

```bash
# Search for mem0-system references in intel-system:
cd /Volumes/Data/ai_projects/intel-system
grep -r "mem0-system" --include="*.yml" --include="*.sh" . | grep -v ".git"

# Search for wingman-system references:
grep -r "wingman-system" --include="*.yml" --include="*.sh" . | grep -v ".git"

# Check docker-compose files don't reference mem0/wingman services:
grep -E "mem0_|wingman_" docker-compose*.yml
```

## ⚠️ DO NOT Remove

- SAP-specific mem0 scripts (they USE mem0, but are SAP workflows)
- Historical documentation in archive/ folders
- Namespace references (intel_system, etc.)
