# CLAUDE.md - Mandatory Development Rules

**Repository:** mem0-system  
**Purpose:** Production mem0 deployment for Mac Studio  
**Last Updated:** 2026-01-09

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

**Violation = IMMEDIATE SECURITY INCIDENT**

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

**Last Major Incident:** 2026-01-03 (reboot outage due to missing auto-start)  
**Prevention:** Rules 1, 3, 8, 9 established to prevent recurrence

---

## 🎯 PHILOSOPHY

**This repository is:**
- Production-focused (PRD + TEST only)
- Self-contained (zero external dependencies)
- Clean and organized (proper file structure)
- Secure (no hardcoded credentials)
- Resilient (auto-recovery, monitoring)

**Keep it that way.**
