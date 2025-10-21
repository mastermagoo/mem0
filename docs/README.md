# mem0 Personal AI Memory System - PRD Deployment

**Version**: 2.0 (Local Neo4j with GDS Plugin)  
**Date**: 2025-10-21  
**Status**: ✅ Production Ready  
**Architecture**: Self-Contained, Zero Dependencies

## 🎯 Overview

mem0 is a personal AI memory system that provides persistent memory capabilities with graph-based knowledge storage. This PRD deployment is completely independent and self-contained.

### Key Features
- **Persistent Memory**: Long-term memory storage and retrieval
- **Graph Knowledge**: Neo4j with Graph Data Science (GDS) plugin
- **Vector Search**: PostgreSQL with pgvector for semantic search
- **Telegram Integration**: Personal memory bot for easy access
- **Monitoring**: Grafana dashboards for system health
- **Zero Dependencies**: No reliance on intel-system or cv-automation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    mem0 PRD Environment                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ mem0_prd    │  │ mem0_neo4j  │  │ mem0_postgres│        │
│  │ :8888       │  │ _prd:7688   │  │ _prd:5433   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐                        │
│  │ mem0_grafana│  │ mem0_telegram│                       │
│  │ _prd:3001   │  │ _bot_prd    │                       │
│  └─────────────┘  └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
│                    mem0_internal Network                    │
│                    192.168.97.0/24                         │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM available
- Ports 3001, 5433, 7475, 7688, 8888 available

### Deployment
```bash
# Clone and navigate to mem0 directory
cd /Volumes/intel-system/deployment/docker/mem0_tailscale

# Deploy all services
docker compose --env-file mem0.env up -d

# Check status
docker compose --env-file mem0.env ps
```

### Verification
```bash
# Test memory creation
curl -X POST http://localhost:8888/memories \
  -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "test memory"}], "user_id": "test"}'

# Check Neo4j GDS functions
docker exec mem0_neo4j_prd cypher-shell -u neo4j -p mem0_neo4j_pass "CALL gds.version()"

# Access Grafana
open http://localhost:3001
```

## 📋 Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| **mem0 API** | `mem0_prd` | 8888 | Main memory API server |
| **Neo4j** | `mem0_neo4j_prd` | 7475/7688 | Graph database with GDS |
| **PostgreSQL** | `mem0_postgres_prd` | 5433 | Vector storage with pgvector |
| **Grafana** | `mem0_grafana_prd` | 3001 | Monitoring dashboards |
| **Telegram Bot** | `mem0_telegram_bot_prd` | - | Personal memory bot |

## 🔧 Configuration

### Environment Variables
Key configuration in `mem0.env`:

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

# Telegram Bot
TELEGRAM_BOT_TOKEN=8199806035:AAE5K_yg6VjFolOl3CGKewuAv52yN47BRz4
```

### Data Storage
- **Location**: `/Users/kermit/mem0-data/`
- **PostgreSQL**: `/Users/kermit/mem0-data/postgres/`
- **Neo4j**: `/Users/kermit/mem0-data/neo4j/`
- **Grafana**: `/Users/kermit/mem0-data/grafana/`

## 🔍 Monitoring

### Health Checks
```bash
# Check all services
docker compose --env-file mem0.env ps

# View logs
docker compose --env-file mem0.env logs mem0

# Test API health
curl http://localhost:8888/docs
```

### Grafana Dashboards
- **URL**: http://localhost:3001
- **Login**: admin/admin
- **Dashboards**: mem0 system metrics, Neo4j performance, PostgreSQL stats

## 🛠️ Operations

### Backup
```bash
# Backup PostgreSQL
docker exec mem0_postgres_prd pg_dump -U mem0_user mem0 > backup_postgres.sql

# Backup Neo4j
docker exec mem0_neo4j_prd neo4j-admin dump --database=neo4j --to=/tmp/backup.dump
docker cp mem0_neo4j_prd:/tmp/backup.dump ./backup_neo4j.dump
```

### Restart Services
```bash
# Restart specific service
docker compose --env-file mem0.env restart mem0

# Restart all services
docker compose --env-file mem0.env restart
```

### Scale/Update
```bash
# Pull latest images
docker compose --env-file mem0.env pull

# Recreate with latest images
docker compose --env-file mem0.env up -d --force-recreate
```

## 🔒 Security

### Network Isolation
- **Internal Network**: `mem0_internal` (192.168.97.0/24)
- **No External Dependencies**: Zero connections to intel-system or cv-automation
- **Port Binding**: All services bound to localhost only

### Authentication
- **Neo4j**: Username/password authentication enabled
- **PostgreSQL**: User-based access control
- **mem0 API**: API key authentication
- **Telegram**: Bot token authentication

## 📚 Documentation

### Core Documentation
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[OPERATIONS.md](OPERATIONS.md)** - Operations and maintenance guide
- **[USER_GUIDE.md](USER_GUIDE.md)** - End-user documentation
- **[API_REFERENCE.md](API_REFERENCE.md)** - API documentation

### Technical Documentation
- **[MEM0_GDS_PATCH_REPORT.md](MEM0_GDS_PATCH_REPORT.md)** - Neo4j GDS integration
- **[LLM_ROUTING.md](LLM_ROUTING.md)** - LLM routing configuration
- **[NAMESPACE_GUIDE.md](NAMESPACE_GUIDE.md)** - Multi-tenant namespace setup

### Troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[LOGS.md](LOGS.md)** - Log analysis guide

## 🚨 Troubleshooting

### Common Issues

**Service Won't Start**
```bash
# Check logs
docker compose --env-file mem0.env logs [service_name]

# Check port conflicts
lsof -i :8888
```

**Neo4j Connection Issues**
```bash
# Test Neo4j connectivity
docker exec mem0_neo4j_prd cypher-shell -u neo4j -p mem0_neo4j_pass "CALL gds.version()"
```

**Memory Creation Fails**
```bash
# Check mem0 logs
docker compose --env-file mem0.env logs mem0 | grep -i error

# Test API directly
curl -X POST http://localhost:8888/memories \
  -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "test"}], "user_id": "test"}'
```

## 📈 Performance

### Resource Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB+ recommended
- **Storage**: 10GB+ for data persistence
- **Network**: Minimal bandwidth requirements

### Optimization
- **PostgreSQL**: Tune `shared_buffers` and `work_mem`
- **Neo4j**: Configure heap size and page cache
- **mem0**: Adjust batch sizes and concurrency limits

## 🔄 Updates & Maintenance

### Version History
- **v2.0** (2025-10-21): Local Neo4j with GDS plugin, zero dependencies
- **v1.0** (2025-09-29): Initial deployment with shared Neo4j

### Update Process
1. Backup current data
2. Pull latest images
3. Update configuration if needed
4. Deploy with `docker compose up -d`
5. Verify functionality

## 📞 Support

### Getting Help
- **Documentation**: Check this README and linked guides
- **Logs**: Review service logs for error details
- **Health Checks**: Use monitoring tools to identify issues

### Contact
- **System**: mem0 Personal AI Memory
- **Environment**: PRD (Production)
- **Architecture**: Self-contained, zero dependencies

---

**✅ mem0 PRD Deployment - Production Ready**  
**Last Updated**: 2025-10-21  
**Status**: Fully Operational
