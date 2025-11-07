# Production Deployment Rules - MANDATORY

**Location**: `/Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale/`
**Status**: ✅ ENFORCED
**Date Created**: 2025-10-30
**Last Updated**: 2025-10-30

---

## 🚨 CRITICAL RULE - ZERO TOLERANCE

### ❌ FORBIDDEN: Direct docker-compose Commands in Production

**NEVER execute these commands directly:**

```bash
# ❌ FORBIDDEN
docker-compose up -d
docker-compose -f docker-compose.prd.yml up -d
docker-compose restart
docker-compose down

# ❌ FORBIDDEN
docker run ...
docker start ...
```

**WHY FORBIDDEN:**
- Wrong compose file may be used (happened Oct 30, 2025)
- Environment variables may not be loaded
- No validation of production requirements
- No audit trail
- Containers may be created on wrong network

**COST OF VIOLATION:** 1-2 hours debugging, service outages, user frustration

---

## ✅ REQUIRED: Use Deployment Wrapper Scripts

### Production Deployments

**ALWAYS use:**

```bash
cd /Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale
./deploy_prd.sh {up|down|restart|status|logs|validate}
```

**Examples:**

```bash
# Start all services
./deploy_prd.sh up

# Restart all services
./deploy_prd.sh restart

# Stop all services
./deploy_prd.sh down

# Check status
./deploy_prd.sh status

# Show logs
./deploy_prd.sh logs
./deploy_prd.sh logs mem0  # specific service

# Validate deployment
./deploy_prd.sh validate
```

---

## 🔒 4-Layer Enforcement System

### Layer 1: CLAUDE.md Mandatory Rule

**Section Added**: 11.1 Production Deployment Enforcement

Claude AI MUST:
- ✅ Always verify production environment before deployment
- ✅ Always use `deploy_prd.sh` wrapper for production
- ✅ Never use direct docker-compose commands in production
- ✅ Validate container labels match deployment file
- ❌ Never skip validation steps

### Layer 2: Deployment Wrapper Script

**File**: `deploy_prd.sh` (7.7KB, executable)

**Enforces:**
1. Correct compose file (`docker-compose.prd.yml`)
2. Correct environment file (`.env` with `DEPLOYMENT_ENV=prd`)
3. Required credentials present
4. Network validation
5. Container label validation
6. Health check validation

**Exit Codes:**
- `0` = Success
- `1` = Validation failed (deployment blocked)

### Layer 3: Compose File Validation Markers

**Added to docker-compose.prd.yml:**

```yaml
environment:
  DEPLOYMENT_ENV: ${DEPLOYMENT_ENV:?Must set DEPLOYMENT_ENV=prd in .env}
```

**Effect:** Container will NOT start if `DEPLOYMENT_ENV=prd` is missing from `.env`

**Error Message:**
```
ERROR: Missing mandatory value for "environment": DEPLOYMENT_ENV: Must set DEPLOYMENT_ENV=prd in .env
```

### Layer 4: Container Labels

**Added to all production containers:**

```yaml
labels:
  - "com.intel-system.compose-file=docker-compose.prd.yml"
  - "com.intel-system.environment=production"
```

**Audit Command:**

```bash
# Check which compose file created containers
docker ps --filter "label=com.intel-system.compose-file=docker-compose.prd.yml"

# Check environment label
docker ps --filter "label=com.intel-system.environment=production"
```

---

## 📋 Pre-Deployment Checklist

Before ANY production deployment, verify:

- [ ] `.env` file exists with `DEPLOYMENT_ENV=prd`
- [ ] All required credentials present in `.env`
- [ ] Using `deploy_prd.sh` wrapper (NOT direct docker-compose)
- [ ] Backups created (if major change)
- [ ] Affected projects notified (intel-sys, wingman, cv-automation, accounting)
- [ ] Downtime window communicated (if applicable)

---

## 🔍 Validation Commands

### Verify Deployment is Correct

```bash
# 1. Check containers have correct labels
docker ps --filter "label=com.intel-system.compose-file=docker-compose.prd.yml" \
          --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# Expected: All mem0_*_prd containers

# 2. Check containers are on correct network
docker network inspect mem0_internal --format '{{range .Containers}}{{.Name}} {{end}}'

# Expected: mem0_postgres_prd mem0_server_prd mem0_grafana_prd mem0_neo4j_prd mem0_telegram_bot_prd

# 3. Verify DEPLOYMENT_ENV
docker exec mem0_server_prd env | grep DEPLOYMENT_ENV

# Expected: DEPLOYMENT_ENV=prd

# 4. Check API health
curl -fsS http://localhost:8888/health

# Expected: {"status":"ok"}
```

---

## 🐛 Troubleshooting Wrong Deployment

### Symptom: Containers on Wrong Network

**Check:**
```bash
docker inspect mem0_server_prd --format '{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}'
docker inspect mem0_postgres_prd --format '{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}'
```

If different networks → deployed with wrong compose file

**Fix:**
```bash
./deploy_prd.sh down
./deploy_prd.sh up
./deploy_prd.sh validate
```

### Symptom: Missing DEPLOYMENT_ENV

**Check:**
```bash
docker exec mem0_server_prd env | grep DEPLOYMENT_ENV
```

If missing → deployed without .env file

**Fix:**
```bash
# Add to .env file
echo "DEPLOYMENT_ENV=prd" >> .env

# Redeploy
./deploy_prd.sh restart
```

### Symptom: Wrong Compose File Used

**Check:**
```bash
docker inspect mem0_server_prd --format '{{index .Config.Labels "com.intel-system.compose-file"}}'
```

If not `docker-compose.prd.yml` → deployed with direct docker-compose

**Fix:**
```bash
./deploy_prd.sh down
./deploy_prd.sh up
```

---

## 📚 Related Documentation

- **Rebuild Guide**: `REBUILD_GUIDE.md` - How to rebuild mem0 container from scratch
- **Data Persistence**: `DATA_PERSISTENCE_GUARANTEE.md` - Why data is safe during rebuilds
- **Deployment Script**: `deploy_prd.sh` - Production deployment wrapper
- **Compose File**: `docker-compose.prd.yml` - Production configuration

---

## ⚠️ Incident History

### Incident 1: Wrong Network (Oct 30, 2025)

**Problem:** mem0_server_prd created on `mem0_internal_prd` network, but postgres on `mem0_internal`

**Root Cause:**
- Oct 25: Containers created with `docker-compose.yml` (base file) → `mem0_internal` network
- Oct 30: mem0 rebuilt with `docker-compose.prd.yml` → `mem0_internal_prd` network
- Network mismatch prevented API from connecting to database

**Impact:**
- 2+ hours debugging
- mem0 API completely down
- All dependent projects affected (intel-sys, wingman, cv-automation, accounting)

**Fix Applied:**
1. Standardized all production deployments on `mem0_internal` network
2. Created mandatory deployment wrapper script
3. Added 4-layer enforcement system
4. Added validation markers to prevent wrong deployment

**Prevention:**
- ✅ Use `deploy_prd.sh` (enforces correct file)
- ✅ Validate container labels
- ✅ Check network consistency
- ✅ Never use direct docker-compose in production

---

## 🎯 Success Criteria

A valid production deployment must meet ALL criteria:

1. ✅ Deployed using `deploy_prd.sh` wrapper
2. ✅ All containers have label: `com.intel-system.compose-file=docker-compose.prd.yml`
3. ✅ All containers have label: `com.intel-system.environment=production`
4. ✅ All containers on `mem0_internal` network
5. ✅ All containers have `DEPLOYMENT_ENV=prd` environment variable
6. ✅ Health checks passing
7. ✅ API endpoints responding
8. ✅ No hardcoded credentials in compose file

**Validation Command:**

```bash
./deploy_prd.sh validate
```

Expected output: `✅ PRODUCTION DEPLOYMENT VALIDATED`

---

## 💡 Best Practices

### DO:
- ✅ Always use `deploy_prd.sh` for production
- ✅ Validate deployment after changes
- ✅ Check container labels match expected values
- ✅ Verify network consistency
- ✅ Test health endpoints after deployment
- ✅ Create backups before major changes
- ✅ Document deviations from standard deployment

### DON'T:
- ❌ Never use direct docker-compose commands
- ❌ Never skip validation steps
- ❌ Never deploy without .env file
- ❌ Never hardcode credentials
- ❌ Never create containers on wrong network
- ❌ Never deploy without checking dependent projects

---

## 🔄 Rollback Procedure

If deployment fails:

```bash
# 1. Stop failed deployment
./deploy_prd.sh down

# 2. Restore previous compose file (if modified)
git checkout deployment/docker/mem0_tailscale/docker-compose.prd.yml

# 3. Redeploy from known good state
./deploy_prd.sh up

# 4. Validate
./deploy_prd.sh validate
```

---

## 📞 Support

**If deployment validation fails:**

1. Run diagnostic: `./deploy_prd.sh validate`
2. Check logs: `./deploy_prd.sh logs`
3. Review this document's troubleshooting section
4. Verify all 4 enforcement layers are active
5. Check git history for compose file changes

**Common Issues:**
- Missing `.env` file → Create with `DEPLOYMENT_ENV=prd`
- Wrong network → Redeploy with `deploy_prd.sh`
- Missing labels → Containers deployed directly, redeploy with wrapper
- Health check fails → Check logs, verify credentials

---

**Last Updated**: 2025-10-30 17:00 CET
**Status**: ✅ ACTIVE - All 4 enforcement layers operational
**Maintained By**: Claude AI + Mark Carey
**Version**: 1.0

