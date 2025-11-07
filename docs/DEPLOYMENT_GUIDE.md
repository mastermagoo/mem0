# mem0 PRD Deployment Guide

**Version**: 2.0 (Local Neo4j with GDS Plugin)  
**Date**: 2025-10-21  
**Architecture**: Self-Contained, Zero Dependencies

## 🎯 Deployment Overview

This guide covers the complete deployment of mem0 Personal AI Memory System in PRD (Production) environment with local Neo4j and zero external dependencies.

## 📋 Prerequisites

### System Requirements
- **OS**: macOS (tested on Mac Studio M1 Max)
- **Docker**: 20.10+ with Docker Compose 2.0+
- **RAM**: 4GB+ available
- **Storage**: 10GB+ free space
- **Network**: Ports 3001, 5433, 7475, 7688, 8888 available

### Software Dependencies
```bash
# Verify Docker installation
docker --version
docker compose version

# Verify ports are available
lsof -i :8888  # mem0 API
lsof -i :5433  # PostgreSQL
lsof -i :7475  # Neo4j HTTP
lsof -i :7688  # Neo4j Bolt
lsof -i :3001  # Grafana
```

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Environment

```bash
# Navigate to mem0 directory
cd /Volumes/intel-system/deployment/docker/mem0_tailscale

# Verify configuration files exist
ls -la mem0.env docker-compose.yml
```

### Step 2: Review Configuration

**Key Configuration Files:**
- `mem0.env` - Environment variables
- `docker-compose.yml` - Service definitions
- `mem0_gds_patch_v2.py` - Neo4j GDS compatibility patch
- `start_mem0_with_patch.sh` - Startup script with patch

**Critical Environment Variables:**
```bash
# Neo4j (Local)
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=mem0_neo4j_pass

# PostgreSQL (Local)
POSTGRES_HOST=postgres
POSTGRES_USER=mem0_user
POSTGRES_PASSWORD=hell0_007

# mem0 API
MEM0_API_KEY=mem0-b0539021-c9a6-4aaa-9193-665f63851a0d
MEM0_PORT=8888

# Container Naming (PRD)
MEM0_CONTAINER_NAME=mem0_prd
POSTGRES_CONTAINER_NAME=mem0_postgres_prd
NEO4J_CONTAINER_NAME=mem0_neo4j_prd
GRAFANA_CONTAINER_NAME=mem0_grafana_prd
TELEGRAM_BOT_CONTAINER_NAME=mem0_telegram_bot_prd
```

### Step 3: Deploy Services

```bash
# Deploy all services
docker compose --env-file mem0.env up -d

# Monitor startup
docker compose --env-file mem0.env logs -f
```

**Expected Output:**
```
Network mem0_internal  Creating
Network mem0_internal  Created
Container mem0_postgres_prd  Creating
Container mem0_neo4j_prd  Creating
Container mem0_grafana_prd  Creating
Container mem0_prd  Creating
Container mem0_telegram_bot_prd  Creating
```

### Step 4: Verify Deployment

```bash
# Check all services are running
docker compose --env-file mem0.env ps

# Expected status: All containers "Up" and "healthy"
```

**Service Status Check:**
```bash
NAME                    STATUS
mem0_prd                Up (healthy)
mem0_neo4j_prd          Up (healthy)
mem0_postgres_prd       Up (healthy)
mem0_grafana_prd         Up
mem0_telegram_bot_prd    Up
```

### Step 5: Test Functionality

#### Test 1: Neo4j GDS Functions
```bash
# Test GDS plugin installation
docker exec mem0_neo4j_prd cypher-shell -u neo4j -p mem0_neo4j_pass "CALL gds.version()"

# Expected output: "2.6.9"

# Test similarity functions
docker exec mem0_neo4j_prd cypher-shell -u neo4j -p mem0_neo4j_pass "RETURN gds.similarity.cosine([1.0, 2.0], [1.0, 2.0])"

# Expected output: 1.0
```

#### Test 2: Memory Creation
```bash
# Test memory creation API
curl -X POST http://localhost:8888/memories \
  -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "test memory creation"}], "user_id": "test_user"}'

# Expected output: JSON with memory creation results
```

#### Test 3: API Documentation
```bash
# Access API docs
open http://localhost:8888/docs

# Or via curl
curl http://localhost:8888/docs
```

#### Test 4: Grafana Monitoring
```bash
# Access Grafana
open http://localhost:3001

# Login: admin/admin
# Check for mem0 dashboards
```

## 🔧 Configuration Details

### Docker Compose Services

#### mem0 API Server
```yaml
mem0:
  image: mem0-fixed:local
  container_name: mem0_prd
  depends_on:
    postgres:
      condition: service_healthy
    neo4j:
      condition: service_healthy
  environment:
    NEO4J_URI: bolt://neo4j:7687
    POSTGRES_HOST: postgres
    # ... other environment variables
  networks:
    - mem0_internal
```

#### Neo4j with GDS Plugin
```yaml
neo4j:
  image: neo4j:5.13.0
  container_name: mem0_neo4j_prd
  environment:
    NEO4J_AUTH: neo4j/mem0_neo4j_pass
    NEO4J_PLUGINS: '["graph-data-science"]'
    NEO4J_dbms_security_procedures_unrestricted: gds.*
  networks:
    - mem0_internal
```

#### PostgreSQL with pgvector
```yaml
postgres:
  image: pgvector/pgvector:pg17
  container_name: mem0_postgres_prd
  environment:
    POSTGRES_DB: mem0
    POSTGRES_USER: mem0_user
    POSTGRES_PASSWORD: hell0_007
  networks:
    - mem0_internal
```

### Network Configuration
```yaml
networks:
  mem0_internal:
    driver: bridge
    name: mem0_internal
```

**Network Details:**
- **Subnet**: 192.168.97.0/24
- **Gateway**: 192.168.97.1
- **Isolation**: Complete - no external network dependencies

## 📊 Data Storage

### Volume Mounts
```bash
# Data directory structure
/Users/kermit/mem0-data/
├── postgres/          # PostgreSQL data
├── neo4j/            # Neo4j data
│   ├── data/         # Database files
│   ├── logs/         # Log files
│   └── plugins/      # Plugin files
└── grafana/          # Grafana data
```

### Backup Strategy
```bash
# PostgreSQL backup
docker exec mem0_postgres_prd pg_dump -U mem0_user mem0 > backup_postgres.sql

# Neo4j backup
docker exec mem0_neo4j_prd neo4j-admin dump --database=neo4j --to=/tmp/backup.dump
docker cp mem0_neo4j_prd:/tmp/backup.dump ./backup_neo4j.dump
```

## 🔍 Monitoring & Health Checks

### Service Health Checks
```bash
# Check all services
docker compose --env-file mem0.env ps

# Check specific service logs
docker compose --env-file mem0.env logs mem0
docker compose --env-file mem0.env logs neo4j
docker compose --env-file mem0.env logs postgres
```

### API Health Check
```bash
# Test API endpoint
curl http://localhost:8888/docs

# Test memory API
curl -X GET http://localhost:8888/memories?user_id=test_user
```

### Grafana Monitoring
- **URL**: http://localhost:3001
- **Login**: admin/admin
- **Dashboards**: System metrics, Neo4j performance, PostgreSQL stats

## 🚨 Troubleshooting

### Common Issues

#### Issue 1: Port Conflicts
```bash
# Check port usage
lsof -i :8888
lsof -i :5433
lsof -i :7475
lsof -i :7688
lsof -i :3001

# Kill conflicting processes
sudo kill -9 [PID]
```

#### Issue 2: Container Won't Start
```bash
# Check logs
docker compose --env-file mem0.env logs [service_name]

# Check container status
docker compose --env-file mem0.env ps

# Restart specific service
docker compose --env-file mem0.env restart [service_name]
```

#### Issue 3: Neo4j Connection Issues
```bash
# Test Neo4j connectivity
docker exec mem0_neo4j_prd cypher-shell -u neo4j -p mem0_neo4j_pass "CALL gds.version()"

# Check Neo4j logs
docker compose --env-file mem0.env logs neo4j
```

#### Issue 4: Memory Creation Fails
```bash
# Check mem0 logs
docker compose --env-file mem0.env logs mem0 | grep -i error

# Test API directly
curl -X POST http://localhost:8888/memories \
  -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "test"}], "user_id": "test"}'
```

### Log Analysis
```bash
# View all logs
docker compose --env-file mem0.env logs

# Follow logs in real-time
docker compose --env-file mem0.env logs -f

# View specific service logs
docker compose --env-file mem0.env logs mem0 --tail 50
```

## 🔄 Maintenance Operations

### Restart Services
```bash
# Restart all services
docker compose --env-file mem0.env restart

# Restart specific service
docker compose --env-file mem0.env restart mem0
```

### Update Images
```bash
# Pull latest images
docker compose --env-file mem0.env pull

# Recreate with latest images
docker compose --env-file mem0.env up -d --force-recreate
```

### Clean Up
```bash
# Stop all services
docker compose --env-file mem0.env down

# Remove volumes (WARNING: This deletes all data)
docker compose --env-file mem0.env down -v

# Remove images
docker compose --env-file mem0.env down --rmi all
```

## ✅ Deployment Verification Checklist

- [ ] All containers are running and healthy
- [ ] Neo4j GDS plugin is installed (version 2.6.9)
- [ ] Memory creation API works
- [ ] Grafana is accessible
- [ ] Telegram bot is running
- [ ] No external network dependencies
- [ ] Data persistence is working
- [ ] Logs show no critical errors

## 📞 Support

### Getting Help
1. Check service logs for error details
2. Verify all prerequisites are met
3. Test individual components
4. Review this deployment guide

### Contact Information
- **System**: mem0 Personal AI Memory
- **Environment**: PRD (Production)
- **Architecture**: Self-contained, zero dependencies

---

**✅ mem0 PRD Deployment Guide**  
**Last Updated**: 2025-10-21  
**Status**: Production Ready
