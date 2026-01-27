# CLAUDE.md - Mandatory Development Rules

**Repository:** mem0-system
**Purpose:** Production mem0 deployment for Mac Studio
**Last Updated:** 2026-01-27

---

## 🚨 CRITICAL RULES - NEVER VIOLATE

### RULE 1: CLEAN ROOT DIRECTORY (MANDATORY)

**The repository root MUST contain ONLY:**

#### **Required Configuration Files:**
- `README.md` - Project readme
- `LICENSE` - License file
- `.gitignore` - Git ignore rules
- `CLAUDE.md` - This file (development rules)

#### **Required Deployment Files:**
- `docker-compose.prd.yml` - Production compose
- `docker-compose.test.yml` - Test compose
- `Dockerfile.mem0` - Custom image build
- `deploy_prd.sh` - Production deployment script
- `com.mem0.prd.plist` - launchd auto-start service

#### **Required Environment Files:**
- `.env` - Production config (git-ignored)
- `.env.test` - Test config (git-ignored)
- `.env.example` / `env.example` - Environment template

#### **Allowed Directories ONLY:**
- `scripts/` - Operational scripts (backup, monitoring, utilities)
- `lib/` - Python modules and application code
- `utils/` - Utility functions and helpers
- `docs/` - All documentation
- `telegram_bot/` - Telegram bot implementation
- `monitoring/` - Monitoring configs (Prometheus, Grafana)
- `tests/` - Test scripts
- `archive/` - Archived files (dev, old configs)
- `deployment/` - Deployment artifacts
- `.git/` - Git repository data
- `.dr-data/` - Disaster recovery data

#### **FORBIDDEN in Root:**
- ❌ NO loose Python files (`.py`) - must be in `lib/`
- ❌ NO loose shell scripts (`.sh`) - must be in `scripts/`
- ❌ NO markdown docs - must be in `docs/`
- ❌ NO test files - must be in `tests/`
- ❌ NO temporary files
- ❌ NO backup files (`.bak`, `.old`, `.tmp`)
- ❌ NO development artifacts

**ENFORCEMENT:**
- Before ANY commit, verify root is clean
- Use `ls -la | grep -v "^d" | wc -l` - should be ≤ 15 files
- Any new file in root requires explicit justification

---

### RULE 2: NO HARDCODED CREDENTIALS (SECURITY)

**NEVER commit or hardcode:**
- Passwords
- API keys
- Tokens
- Client secrets
- Database credentials
- Private keys
- Telegram tokens

**ALL credentials MUST:**
- Be in `.env` files (git-ignored)
- Use environment variables in code: `${VAR_NAME:?required}`
- Use placeholders in examples: `REPLACE_ME` or `your_token_here`

**ALL configuration values MUST:**
- Use environment variables for ports, URLs, database names
- NO hardcoded ports (e.g., `localhost:8888`) - use `${MEM0_PORT}`
- NO hardcoded credentials in connection strings
- Single source of truth: `.env` file for all config
- Scripts MUST read from environment or `.env`

**Violation = IMMEDIATE SECURITY INCIDENT / OPERATIONAL FAILURE**

---

### RULE 3: ZERO EXTERNAL DEPENDENCIES (ISOLATION)

**This repository MUST be 100% self-contained:**

- ❌ NO references to `/Volumes/Data/ai_projects/intel-system`
- ❌ NO references to `/Volumes/Data/ai_projects/wingman-system`
- ❌ NO `../../` paths that go outside this repo
- ❌ NO external service dependencies (e.g., `intel-llm-router`)
- ✅ ALL scripts in `./scripts/`
- ✅ ALL configs in this repo
- ✅ ALL dependencies declared in requirements.txt or Dockerfile

**Exception:** Host-level services (Docker, Ollama on host.docker.internal)

---

### RULE 4: PROPER FILE ORGANIZATION

**Python Files:**
- Application code → `lib/`
- Utilities → `utils/`
- Tests → `tests/`

**Shell Scripts:**
- Operational scripts → `scripts/`
- Deployment → `deploy_prd.sh` (root only)

**Documentation:**
- Deployment guides → `docs/deployment/`
- Operations → `docs/operations/`
- Architecture → `docs/`
- Historical → `docs/archive/`

**Configuration:**
- Docker compose → Root (docker-compose.*.yml)
- Monitoring → `monitoring/`
- Environment → `.env` files (root, git-ignored)

---

### RULE 5: DOCKER LABELS & NAMING

**All containers MUST use:**
- Labels: `com.mem0-system.*` (NOT `com.intel-system`)
- Network: `mem0_internal_*` (environment-specific)
- Container names: `mem0_*_prd` or `mem0_*_test`

**Images MUST:**
- Use custom builds: `mem0-fixed:local`
- Be built from Dockerfiles in THIS repo
- NOT use upstream images in production

---

### RULE 6: DOCUMENTATION REQUIREMENTS

**When creating documentation:**
- ❌ NEVER create new files in root
- ✅ ALWAYS use existing docs or add to `docs/`
- ✅ Update existing guides, don't duplicate
- ✅ Use proper directory structure

**Documentation structure:**
```
docs/
├── deployment/     (deployment guides)
├── operations/     (operational procedures)
├── archive/        (historical/deprecated)
├── *.md            (main documentation)
```

---

### RULE 7: GIT COMMIT RULES

**Before EVERY commit:**
1. Verify root directory is clean
2. Check NO hardcoded credentials
3. Ensure NO external dependencies
4. Run linting/validation if available
5. Test deployment if config changed

**Commit message format:**
```
type: brief description

- Detailed change 1
- Detailed change 2

Refs: #issue (if applicable)
```

**NEVER commit:**
- `.env` files (use `.gitignore`)
- Credentials or secrets
- Temporary files
- IDE-specific files (already in `.gitignore`)

---

### RULE 8: DEPLOYMENT SAFETY

**Production deployment MUST:**
- Use `./deploy_prd.sh` (NEVER direct docker-compose)
- Require `.env` with `DEPLOYMENT_ENV=prd`
- Validate environment before starting
- Check health after deployment
- Support rollback

**Test deployment MUST:**
- Use isolated ports (15432, 18888, etc.)
- Use separate network (`mem0_internal_test`)
- Use separate data directory
- NOT conflict with PRD

---

### RULE 9: MONITORING & ALERTING

**REQUIRED monitoring:**
- Health checks every 5 minutes
- Backups daily at 2:30 AM
- Auto-start via launchd
- Telegram alerts on failures

**Scripts MUST:**
- Be in `scripts/` directory
- Have execute permissions
- Be self-contained (no external deps)
- Source config from `.env`

---

### RULE 10: PATH CONVENTIONS

**All paths MUST be:**
- Absolute paths in scripts: `/Volumes/Data/ai_projects/mem0-system/...`
- Relative paths in configs: `./lib/`, `./scripts/`, etc.
- Environment-variable driven where possible

**Container paths:**
- Data: `/app/data`
- Patches: `/app/*.py`
- Scripts: `/app/*.sh`

---

## 🔧 ENFORCEMENT CHECKLIST

Before any code change:
- [ ] Root directory contains ≤ 15 files
- [ ] No `.py` or `.sh` files in root (except deploy_prd.sh)
- [ ] No credentials in any files
- [ ] No references to intel-system or wingman-system
- [ ] All new docs in `docs/` subdirectories
- [ ] Docker labels use `com.mem0-system`
- [ ] Changes tested in test environment

---

## 📋 QUICK VERIFICATION

```bash
# Check root is clean (should be ≤ 15 files)
ls -la | grep -v "^d" | wc -l

# Check no credentials
grep -r "password\|secret\|key" --include="*.yml" --include="*.py" | grep -v "REPLACE_ME\|your_\|:?"

# Check no external deps
grep -r "intel-system\|wingman-system\|../../" --include="*.yml" --include="*.sh"

# Verify structure
tree -L 1 -d
```

---

## ⚠️ VIOLATION CONSEQUENCES

**If rules are violated:**
1. Immediate rollback of changes
2. Fix violations before proceeding
3. Update this document if rule needs clarification
4. Document lesson learned

**No exceptions** - these rules exist to prevent production outages and security incidents.

---

## 📚 INCIDENT HISTORY & LEARNINGS

### Incident: 2026-01-27 - Complete Data Loss (CRITICAL)

**Summary:** Complete data loss (1,968 memories) due to Docker container recreation with incompatible credentials and embedding model changes. Successfully restored from backup.

**Root Cause:**
1. Containers recreated on 2026-01-10 with new credentials (mem0_user → mem0_user_prd)
2. Embedding model switched from OpenAI (1536 dims) to Ollama (768 dims) on 2026-01-07
3. Result: Fresh empty database created, old data inaccessible

**Contributing Factors:**
- Hardcoded ports in scripts (localhost:8888 vs actual 8889/18888)
- Silent sync failures (scripts never connected, no error logging)
- No data validation in backups (backed up empty database for 17 days)
- No monitoring alerts (memory count dropped from 1,968 → 0 with no alerts)
- Insufficient self-healing (only restarted containers, didn't validate data)

**Prevention Measures Implemented:**
1. ✅ Fixed hardcoded ports in all operational scripts (deploy_prd.sh, rebuild_mem0.sh, etc.)
2. ✅ Created comprehensive incident documentation (docs/incidents/2026-01-27_DATA_LOSS_RESTORATION.md)
3. ⏳ Add Grafana alerts for memory count = 0 or drops >50%
4. ⏳ Add backup validation (verify data before saving)
5. ⏳ Add automatic restore mechanism for empty database detection
6. ⏳ Document safe container recreation procedure

**Key Learnings:**
- **Data-aware monitoring** - Monitor what matters (data), not just containers
- **Backup validation** - Verify backups contain actual data before overwriting
- **Configuration management** - Single source of truth for credentials/ports, no hardcoding
- **Better logging** - Failed connections must log errors and alert
- **Regular DR testing** - Test restore process monthly, not just backup

**Full Details:** `/Volumes/Data/ai_projects/mem0-system/docs/incidents/2026-01-27_DATA_LOSS_RESTORATION.md`

---

### Incident: 2026-01-03 - Reboot Outage

**Summary:** Auto-start failure after reboot due to missing launchd configuration.

**Prevention:** Rules 1, 3, 8, 9 established; `com.mem0.prd.plist` created for auto-start.

---

## 🎯 PHILOSOPHY

**This repository is:**
- Production-focused (PRD + TEST only)
- Self-contained (zero external dependencies)
- Clean and organized (proper file structure)
- Secure (no hardcoded credentials)
- Resilient (auto-recovery, monitoring)

**Keep it that way.**
