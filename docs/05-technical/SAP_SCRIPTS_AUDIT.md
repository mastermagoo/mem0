# SAP Scripts Audit - Complete Analysis

**Date:** 2026-01-12  
**Status:** 🔍 Audit Complete - Reorganization Required

---

## 🎯 Executive Summary

**Problem:** SAP-related scripts are mixed between RAG (ChromaDB) and mem0 (memory system) functionality.

**Finding:** 
- **ALL scripts in "05-Technical-SAP REPO" folder are RAG-related** (ChromaDB indexing)
- **NO mem0 sync scripts found** in this folder
- mem0 sync scripts are in: `/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP/docs/00-strategic/mem0/`
- These scripts should be moved to mem0-system repo

---

## 📋 Script Inventory

### ✅ RAG Scripts (ChromaDB - Should Move to intel-system)

All 13 scripts in this folder index SAP documents into ChromaDB:

**Shell Scripts (7):**
1. `auto_index_new_files.sh` - Auto-indexes new/modified files (cron: hourly)
2. `index_all_now.sh` - Manual full indexing
3. `index_all_robust.sh` - Robust full indexing with verification
4. `index_all_working.sh` - Working version
5. `index_sap_rag_prd.sh` - RAG pipeline indexing (HTTP endpoints)
6. `index_sap_via_container.sh` - Container-based indexing
7. `setup_auto_indexing.sh` - Sets up cron job

**Python Scripts (6):**
1. `index_sap_standalone.py` - Standalone indexer
2. `index_sap_final.py` - Final container-based indexer
3. `index_sap_documents.py` - HTTP-based indexer
4. `index_sap_container.py` - Container-based indexer
5. `rag_query.py` - RAG query script
6. `rag_demo_tomorrow.py` - Demo script

**All use:** `intel-chromadb-prd` container (NOT mem0)

---

## 🔍 mem0 Scripts (Missing from This Folder)

**Location:** `/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP/docs/00-strategic/mem0/`

**Scripts That Should Be in mem0-system:**

1. `scheduled_sync_job.sh` - Main sync job (cron: 2:00 AM daily)
   - **Calls:** `http://localhost:8888/memories` ❌ **WRONG PORT**
   - **Should call:** `http://localhost:8889` (actual mem0 port)

2. `comprehensive_sap_sync.sh` - Comprehensive sync
3. `multi_client_sync.sh` - Multi-client sync
4. `monitoring/get_memory_count.sh` - Memory count checker
5. `monitoring/mem0_daily_heartbeat.sh` - Daily heartbeat
6. `monitoring/capacity_forecast.sh` - Capacity forecasting
7. `monitoring/mem0_sync_daily_report.sh` - Daily sync report
8. `monitoring/mem0_daily_status_notification.sh` - Status notification
9. `monitoring/mem0_daily_closure_notification.sh` - Closure notification
10. `intelligence/daily_automation_system.sh` - Daily automation
11. `intelligence/monday_prep_automation.sh` - Monday prep
12. `intelligence/post_meeting_mem0_auto.sh` - Post-meeting automation

---

## 🚨 Critical Issues Found

### 1. Port Mismatch (CRITICAL)
- **mem0 server runs on:** `127.0.0.1:8889` (verified healthy)
- **Scripts call:** `http://localhost:8888` ❌
- **Result:** "mem0 server not responding" errors

**Fix Required:**
- Update all mem0 API calls to use port 8889
- OR change mem0 to run on port 8888 (update `.env` and restart)

### 2. Scripts in Wrong Location
- **RAG scripts** (ChromaDB) are in mem0-system repo ❌
- **mem0 scripts** are in intel-system repo ❌

**Should be:**
- RAG scripts → intel-system (they use intel-chromadb-prd container)
- mem0 scripts → mem0-system (they use mem0 API)

### 3. Cron Jobs Point to Old Locations
All cron jobs still point to intel-system paths for mem0 scripts.

### 4. Missing Scripts in mem0-system
The mem0 sync scripts are NOT in this repo. They need to be:
- Copied from intel-system
- Fixed for port 8889
- Placed in `scripts/sap/` directory

---

## 📊 Current Cron Job Analysis

**mem0-system Cron Jobs (✅ Correct):**
- Backup: `30 2 * * *` and `0 3 * * 0`
- Health monitor: `*/5 * * * *`

**intel-system Cron Jobs (⚠️ Need Review):**
- mem0 sync: `0 2 * * *` → Should move to mem0-system
- RAG indexing: `0 * * * *` → Should stay in intel-system
- mem0 monitoring: Multiple jobs → Should move to mem0-system
- SAP automation: Business logic → Can stay in intel-system

---

## 🎯 Reorganization Plan

### Phase 1: Move RAG Scripts to intel-system
Move all scripts from `docs/05-technical/05-Technical-SAP REPO/` to intel-system.

### Phase 2: Copy mem0 Scripts to mem0-system
Copy mem0 sync/monitoring scripts from intel-system to `scripts/sap/`.

**Required Changes:**
1. Fix port from 8888 → 8889 (or use env var)
2. Update paths to use mem0-system repo
3. Update API endpoints to use correct port

### Phase 3: Fix Port Configuration
**Option A:** Change mem0 to run on port 8888 (recommended)
**Option B:** Update all scripts to use port 8889

### Phase 4: Update Cron Jobs
Update crontab to point to new locations in mem0-system.

---

## ✅ Verification Checklist

- [ ] All RAG scripts moved to intel-system
- [ ] All mem0 scripts copied to mem0-system
- [ ] Port configuration fixed (8888 or 8889, consistent)
- [ ] All cron jobs updated to new paths
- [ ] Scripts tested manually
- [ ] Cron jobs verified working
- [ ] Documentation updated

---

**Last Updated:** 2026-01-12  
**Status:** Audit Complete - Awaiting Reorganization
on port 8888 (update `.env` and restart)

### 2. Scripts in Wrong Location
- **RAG scripts** (ChromaDB) are in mem0-system repo ❌
- **mem0 scripts** are in intel-system repo ❌
- **Should be:**
  - RAG scripts → intel-system (they use intel-chromadb-prd container)
  - mem0 scripts → mem0-system (they use mem0 API)

### 3. Cron Jobs Point to Old Locations
All cron jobs still point to intel-system paths:
```bash
# Current (WRONG):
0 2 * * * /Volumes/Data/ai_projects/intel-system/.../scheduled_sync_job.sh
0 * * * * /Volumes/Data/ai_projects/intel-system/.../auto_index_new_files.sh

# Should be:
0 2 * * * /Volumes/Data/ai_projects/mem0-system/scripts/sap/scheduled_sync_job.sh
0 * * * * /Volumes/Data/ai_projects/intel-system/.../auto_index_new_files.sh
```

### 4. Missing Scripts in mem0-system
The mem0 sync scripts referenced in your message are NOT in this repo. They need to be:
- Copied from intel-system
- Fixed for port 8889
- Placed in `scripts/sap/` directory

---

## 📊 Current Cron Job Analysis

### mem0-system Cron Jobs (✅ Correct):
```bash
30 2 * * * /Volumes/Data/ai_projects/mem0-system/scripts/backup_mem0.sh daily
0 3 * * 0 /Volumes/Data/ai_projects/mem0-system/scripts/backup_mem0.sh weekly
*/5 * * * * /Volumes/Data/ai_projects/mem0-system/scripts/health_monitor.sh
```

### intel-system Cron Jobs (⚠️ Need Review):
```bash
# mem0 sync (should move to mem0-system):
0 2 * * * /Volumes/Data/ai_projects/intel-system/.../scheduled_sync_job.sh

# RAG indexing (should stay in intel-system):
0 * * * * /Volumes/Data/ai_projects/intel-system/.../auto_index_new_files.sh

# mem0 monitoring (should move to mem0-system):
0 8 * * * /Volumes/Data/ai_projects/intel-system/.../mem0_daily_heartbeat.sh
0 0 * * * /Volumes/Data/ai_projects/intel-system/.../capacity_forecast.sh record
0 9 * * * /Volumes/Data/ai_projects/intel-system/.../capacity_forecast.sh alert
30 8 * * * /Volumes/Data/ai_projects/intel-system/.../mem0_sync_daily_report.sh
0 9 * * * /Volumes/Data/ai_projects/intel-system/.../mem0_daily_status_notification.sh
0 18 * * * /Volumes/Data/ai_projects/intel-system/.../mem0_daily_closure_notification.sh

# SAP automation (business logic - can stay in intel-system):
0 17 * * * /Volumes/Data/ai_projects/intel-system/.../daily_automation_system.sh
0 18 * * 0 /Volumes/Data/ai_projects/intel-system/.../monday_prep_automation.sh
0 * * * * /Volumes/Data/ai_projects/intel-system/.../post_meeting_mem0_auto.sh
```

---

## 🎯 Reorganization Plan

### Phase 1: Move RAG Scripts to intel-system
**Action:** Move all scripts from `docs/05-technical/05-Technical-SAP REPO/` to intel-system

**Destination:** `/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP/docs/05-technical/`

**Scripts to Move:**
- All `.sh` files (7 scripts)
- All `.py` files (6 scripts)
- All markdown documentation

**Cron Update:** None needed (already points to intel-system)

---

### Phase 2: Copy mem0 Scripts to mem0-system
**Action:** Copy mem0 sync/monitoring scripts from intel-system to mem0-system

**Source:** `/Volumes/Data/ai_projects/intel-system/docs/03-business/clients/SAP/docs/00-strategic/mem0/`

**Destination:** `/Volumes/Data/ai_projects/mem0-system/scripts/sap/`

**Scripts to Copy:**
```
scripts/sap/
├── scheduled_sync_job.sh
├── comprehensive_sap_sync.sh
├── multi_client_sync.sh
└── monitoring/
    ├── get_memory_count.sh
    ├── mem0_daily_heartbeat.sh
    ├── capacity_forecast.sh
    ├── mem0_sync_daily_report.sh
    ├── mem0_daily_status_notification.sh
    └── mem0_daily_closure_notification.sh
└── intelligence/
    ├── daily_automation_system.sh
    ├── monday_prep_automation.sh
    └── post_meeting_mem0_auto.sh
```

**Required Changes:**
1. Fix port from 8888 → 8889 (or use env var)
2. Update paths to use mem0-system repo
3. Update API endpoints to use correct port

---

### Phase 3: Fix Port Configuration
**Option A:** Change mem0 to run on port 8888 (recommended)
- Update `.env`: `MEM0_PORT=8888`
- Restart mem0: `docker compose -f docker-compose.prd.yml restart mem0`
- No script changes needed

**Option B:** Update all scripts to use port 8889
- Update all API calls: `http://localhost:8888` → `http://localhost:8889`
- Use environment variable: `MEM0_API_URL=${MEM0_API_URL:-http://localhost:8889}`

---

### Phase 4: Update Cron Jobs
**Action:** Update crontab to point to new locations

**Changes:**
```bash
# FROM:
0 2 * * * /Volumes/Data/ai_projects/intel-system/.../scheduled_sync_job.sh

# TO:
0 2 * * * /Volumes/Data/ai_projects/mem0-system/scripts/sap/scheduled_sync_job.sh
```

**Repeat for all mem0-related cron jobs**

---

## ✅ Verification Checklist

After reorganization:

- [ ] All RAG scripts moved to intel-system
- [ ] All mem0 scripts copied to mem0-system
- [ ] Port configuration fixed (8888 or 8889, consistent)
- [ ] All cron jobs updated to new paths
- [ ] Scripts tested manually
- [ ] Cron jobs verified working
- [ ] Documentation updated

---

## 📝 Next Steps

1. **Immediate:** Fix port mismatch (choose Option A or B above)
2. **Short-term:** Copy mem0 scripts to mem0-system and fix ports
3. **Medium-term:** Move RAG scripts to intel-system
4. **Long-term:** Update all cron jobs and verify

---

## 🔗 Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Repository rules (no external dependencies)
- [OPERATIONS.md](../OPERATIONS.md) - Operational procedures
- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) - Deployment guide

---

**Last Updated:** 2026-01-12  
**Status:** Audit Complete - Awaiting Reorganization
