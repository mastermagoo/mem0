# 🚀 mem0 PRD - Start Here

**Last Updated:** 2026-01-10 19:35
**Status:** ✅ DEPLOYED & RUNNING (PRD + TEST)

---

## ✅ Current Status

**mem0 PRD is LIVE and HEALTHY!**

- 🟢 API: http://localhost:8889/docs
- 🟢 Grafana: http://localhost:3001
- 🟢 Neo4j: http://localhost:7475
- 🟢 PostgreSQL: localhost:5433

---

## 📚 Documentation Path

1. **[DEPLOYMENT_SUCCESS.md](DEPLOYMENT_SUCCESS.md)** - What was just deployed
2. **[DEPLOYMENT_READY.md](DEPLOYMENT_READY.md)** - Full deployment guide
3. **[INSTALLATION.md](INSTALLATION.md)** - Installation instructions
4. **[../OPERATIONS.md](../OPERATIONS.md)** - Daily operations
5. **[../TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** - Common issues

---

## 🔧 Quick Commands

```bash
# Check status
docker ps --filter "name=mem0.*prd"

# View logs
docker logs mem0_server_prd --tail 50

# Restart
cd /Volumes/Data/ai_projects/mem0-system
./deploy_prd.sh restart

# Health check
/Volumes/Data/ai_projects/mem0-system/scripts/health_monitor.sh
```

---

## ✅ TEST Environment

**mem0 TEST is also available:**

- 🟢 API: http://localhost:18888/docs
- 🟢 Grafana: http://localhost:23010
- 🟢 Neo4j: http://localhost:27474
- 🟢 PostgreSQL: localhost:25432

**Start TEST:**
```bash
cd /Volumes/Data/ai_projects/mem0-system
./scripts/start_test.sh
```

---

**Everything is automated and working!**
