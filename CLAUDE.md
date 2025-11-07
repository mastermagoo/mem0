# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Self-contained **Mem0 Platform** deployment with persistent AI memory system. Standalone infrastructure providing memory services for other AI projects via Docker networking.

**Purpose:** Centralized memory storage with multi-namespace isolation, graph-based memory relationships, and Telegram bot interface.

**Key Technologies:** PostgreSQL (pgvector), Neo4j (Graph Data Science), FastAPI, Docker Compose, Telegram Bot

## Architecture

### Service Stack
- **mem0_prd** - FastAPI-based memory API server (port 8888)
- **postgres** - PostgreSQL with pgvector extension (port 5433)
- **neo4j** - Neo4j with GDS plugin (ports 7474, 7687)
- **grafana** - Monitoring dashboard (port 3001)
- **telegram_bot** - Telegram interface for personal memory access

### Multi-Namespace Architecture
Memory isolation using composite user IDs in format `{user_id}/{namespace}`:
- `mark_carey/progressief` - Business consulting
- `mark_carey/cv_automation` - Job search automation
- `mark_carey/investments` - Investment tracking
- `mark_carey/personal` - Personal notes
- `mark_carey/intel_system` - Infrastructure/AI projects

**Neo4j:** Node labeling with namespace property + compound indexes for O(log n) lookups
**PostgreSQL:** Namespace column with filtered indexes for vector similarity search within namespace boundaries

### Data Storage
All persistent data in: `/Volumes/Data/ai_projects/mem0-platform/data/`
- `data/postgres/` - Vector embeddings and memory metadata
- `data/neo4j/` - Graph relationships between memories
- `data/grafana/` - Monitoring dashboards
- `data/` - Application data (history.db)

### Network Architecture
**Internal Bridge Network:** `mem0_internal`
- Services communicate via container names
- External projects connect via: `external: true, name: mem0_internal`

### External Dependencies

**⚠️ CRITICAL: mem0-platform requires intel-system's Ollama service**

- **Managed By:** intel-system infrastructure at `/Volumes/Data/ai_projects/intel-system`
- **Service:** Ollama (local LLM inference)
- **Endpoint:** `http://host.docker.internal:11434` (from Docker containers)
- **Model Used:** `mistral:7b-instruct-q5_K_M` (Phase 1-5 optimized, Q5_K_M quantization)
- **Embedder:** `nomic-embed-text:latest`
- **Purpose:** Memory creation, search, and graph operations (100% local, $0 cost)
- **Version:** Ollama 0.12.0+ required
- **Health Check:** `ollama list` should show both models available
- **Fallback:** OpenAI configured but unused (100% local achieved)
- **Performance:** 1.6× faster than OpenAI, 25% less RAM, 100% GPU (Metal)

**If Ollama is not running:**
- Memory creation will fail
- Search operations will fail
- Graph operations will fail
- No automatic fallback to OpenAI (by design)

**Monitoring (Updated 2025-10-27):**
- **Unified Monitoring**: mem0-platform is monitored by intel-system's Grafana (port 3000)
- **Metrics Exporter**: Runs on host (port 9092), tracks mem0 + Ollama dependency health
- **Dashboard**: http://localhost:3000/d/b8a5c9d2-ebfa-4a7b-b135-842656ba080d/mem0-platform-dependency-monitoring
- **Prometheus**: Scrapes mem0 metrics every 30s via intel-system Prometheus (port 9090)
- **Alerts**: Ollama dependency failures trigger alerts in intel-system monitoring
- **Standalone Grafana**: mem0's own Grafana (port 3001) still available for local development

**Shared Infrastructure:** intel-system also provides PostgreSQL and Redis for cv-automation project, but mem0-platform is self-contained with its own PostgreSQL and Neo4j instances.

### LLM Integration (Updated 2025-10-27)
**Ollama Connection:** Uses intel-system's optimized Ollama service
- **Host:** `http://host.docker.internal:11434`
- **Model:** `mistral:7b-instruct-q5_K_M` (Phase 1-5 optimized)
- **Embedder:** `nomic-embed-text:latest`
- **Performance:** 1.6× faster, 25% less RAM, 100% GPU (Metal)
- **Cost:** $0/month (100% local, no OpenAI calls)
- **Dependency:** Requires intel-system Ollama service running

**Key Benefits:**
- Leverages Phase 1-5 Ollama optimizations from intel-system
- Q5_K_M quantization for optimal speed/quality balance
- Session caching for 3-6× speedup on repetitive tasks
- Multi-instance parallelism ready (3 workers available)

## Common Development Commands

### Deployment

**Quick Start (Production):**
```bash
cd /Volumes/Data/ai_projects/mem0-platform
bash scripts/deploy.sh
```

**Manual Control:**
```bash
cd docker
docker-compose --env-file ../.env.prd up -d      # Start all services
docker-compose --env-file ../.env.prd down       # Stop services
docker-compose --env-file ../.env.prd ps         # Check status
```

**Environment-Specific:**
```bash
# Development
docker-compose --env-file ../.env.dev.example -f docker-compose.dev.yml up -d

# Test
docker-compose --env-file ../.env.test -f docker-compose.test.yml up -d
```

### Monitoring & Logs

```bash
# Follow all logs
docker-compose --env-file ../.env.prd logs -f

# Specific service
docker-compose --env-file ../.env.prd logs -f mem0_prd
docker-compose --env-file ../.env.prd logs -f neo4j

# Check service health
docker-compose --env-file ../.env.prd ps
```

### Testing

**API Health Check:**
```bash
curl http://localhost:8888/docs
```

**Neo4j GDS Verification:**
```bash
docker exec mem0_neo4j cypher-shell -u neo4j -p <password> "CALL gds.version()"
docker exec mem0_neo4j cypher-shell -u neo4j -p <password> "RETURN gds.similarity.cosine([1.0, 2.0], [1.0, 2.0])"
```

**PostgreSQL Connectivity:**
```bash
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "SELECT COUNT(*) FROM memories;"
```

**Memory API Test:**
```bash
curl -X POST http://localhost:8888/memories \
  -H 'Content-Type: application/json' \
  -d '{"messages": [{"role": "user", "content": "test memory"}], "user_id": "test_user/personal"}'
```

## Key Implementation Details

### Neo4j GDS Patch System
Mem0 uses Neo4j GDS functions that require patching for compatibility. The patch system:
1. **Dockerfile.neo4j** - Builds custom Neo4j image with GDS plugin
2. **scripts/mem0_gds_patch_v2.py** - Python patch applied at startup
3. **scripts/start_mem0_with_patch.sh** - Applies patch before starting mem0 server

The patch runs automatically on container startup via volume mount and custom command in docker-compose.yml:
```yaml
volumes:
  - ../scripts/mem0_gds_patch_v2.py:/app/mem0_gds_patch_v2.py:ro
  - ../scripts/start_mem0_with_patch.sh:/app/start_mem0_with_patch.sh:ro
command: ["/bin/bash", "/app/start_mem0_with_patch.sh"]
```

### LLM Routing Strategy (Updated 2025-10-27)
Mem0 configured for 100% local Ollama routing:
- **Provider:** intel-system Ollama service (Phase 1-5 optimized)
- **Primary Model:** mistral:7b-instruct-q5_K_M (3.8s response, Q5_K_M quantization)
- **Embedder:** nomic-embed-text:latest
- **Connection:** `http://host.docker.internal:11434`
- **Fallback:** OpenAI available but unused (100% local achieved)
- **Configuration:** LLM_ROUTING_ENABLED=true, LLM_LOCAL_THRESHOLD=95
- **Cost:** $0/month (vs $42/month with OpenAI)
- **Performance:** 1.6× faster, 100% GPU (Metal), 25% less RAM

### Telegram Bot Integration
Personal memory access via Telegram:
- Commands: `/store`, `/recall`, `/search`, `/namespace`
- Namespace-aware memory operations
- Built separately: `scripts/telegram_bot/`
- Config: `scripts/telegram_bot/config.py`

## Configuration Management

### Environment Files
- `.env` - Default configuration (gitignored)
- `.env.prd` - Production secrets (gitignored)
- `.env.test` - Test environment
- `.env.dev.example` - Development template
- `.env.example` - Base template

**Required Secrets:**
- `POSTGRES_PASSWORD` - PostgreSQL database password
- `OPENAI_API_KEY` - OpenAI API key for LLM fallback
- `MEM0_API_KEY` - Mem0 API authentication key
- `NEO4J_PASSWORD` - Neo4j database password
- `TELEGRAM_BOT_TOKEN` - Telegram bot token

### Port Configuration
Default ports (configurable via .env):
- 8888 - Mem0 API
- 5433 - PostgreSQL (external)
- 7474 - Neo4j HTTP (external)
- 7687 - Neo4j Bolt (external)
- 3001 - Grafana

## Testing & Integration

**Test Scripts:**
- `scripts/test_integration.py` - Full integration tests
- `scripts/test_llm_routing.py` - LLM routing tests
- `scripts/test_namespace_isolation.py` - Namespace isolation verification

**Integration with CV-Automation:**
Projects connect via shared Docker network. No code changes needed - services discover each other via container names (e.g., `http://mem0_prd:8888`).

## Utility Scripts

- `scripts/deploy.sh` - Automated deployment
- `scripts/namespace_api.py` - Namespace management API
- `scripts/namespace_manager.py` - Namespace utilities
- `scripts/setup_namespaces.sh` - Initialize namespaces in databases
- `scripts/rotate-openai-key.sh` - Rotate OpenAI API key
- `scripts/telegram_bot/` - Telegram bot implementation

## Documentation

Comprehensive documentation in `docs/`:
- **API_REFERENCE.md** - API endpoints and usage
- **DEPLOYMENT_GUIDE.md** - Step-by-step deployment
- **OPERATIONS.md** - Monitoring, backups, maintenance
- **TROUBLESHOOTING.md** - Common issues and solutions
- **NAMESPACE_ARCHITECTURE.md** - Multi-context memory design
- **NAMESPACE_GUIDE.md** - Namespace usage patterns
- **LLM_ROUTING.md** - Local-first LLM strategy
- **USER_GUIDE.md** - End-user documentation

## Security Considerations

1. **Secrets Management:** All credentials in .env files (gitignored)
2. **Network Isolation:** Services isolated in internal Docker network
3. **External Access:** Only defined ports exposed to localhost
4. **API Authentication:** MEM0_API_KEY required for API access
5. **Namespace Isolation:** Enforced at database level with constraints

## Troubleshooting Quick Reference

**Container won't start:**
```bash
docker-compose --env-file ../.env.prd logs [service_name]
lsof -i :[port]  # Check for port conflicts
```

**Neo4j connectivity issues:**
```bash
docker exec mem0_neo4j cypher-shell -u neo4j -p <password> "CALL gds.version()"
docker network inspect mem0_internal
```

**Memory creation failures:**
```bash
docker-compose --env-file ../.env.prd logs mem0_prd | grep -i error
curl http://localhost:8888/docs  # Check API availability
```

## Project History

Migrated from `/Volumes/intel-system/deployment/docker/mem0_tailscale/` to standalone project on 2025-10-21. See MIGRATION_SUMMARY.md for complete migration details.
