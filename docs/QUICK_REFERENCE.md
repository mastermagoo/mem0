# mem0 Server - Quick Reference

## Service Status
```bash
docker compose ps
```

## Access Points
- **API Documentation:** http://localhost:8888/docs
- **Grafana Dashboard:** http://localhost:3001 (admin/admin)
- **Neo4j Browser:** http://localhost:7475 (neo4j/intel123)
- **PostgreSQL:** localhost:5433 (mem0_user/hell0_007)

## Common Commands

### Start/Stop
```bash
docker compose up -d          # Start all services
docker compose down           # Stop all services
docker compose restart mem0   # Restart mem0 server only
```

### Logs
```bash
docker compose logs mem0 --follow     # Follow mem0 logs
docker compose logs --tail=100        # Last 100 lines (all services)
```

### Health Checks
```bash
# Quick health check
curl http://localhost:8888/docs

# Database connectivity
docker exec mem0_postgres psql -U mem0_user -d mem0 -c "SELECT COUNT(*) FROM memories;"

# Neo4j connectivity  
docker exec mem0_server python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://intel-system-intel-neo4j-1:7687', auth=('neo4j', 'intel123')); driver.verify_connectivity(); print('✅ Connected')"
```

## API Usage Examples

### Store Memory
```bash
curl -X POST http://localhost:8888/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I prefer Python for data analysis"},
      {"role": "assistant", "content": "Noted your Python preference"}
    ],
    "user_id": "mark_carey"
  }'
```

### Search Memories
```bash
curl -X POST http://localhost:8888/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "programming languages",
    "user_id": "mark_carey"
  }'
```

### Get All Memories
```bash
curl "http://localhost:8888/memories?user_id=mark_carey"
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs mem0 --tail=50

# Verify environment variables
docker compose config | grep NEO4J

# Test database connections
docker exec mem0_postgres pg_isready -U mem0_user
```

### API Returns Errors
```bash
# Check if server is listening
docker exec mem0_server netstat -tlnp | grep 8888

# Verify OpenAI key (if using LLM features)
# Edit mem0.env and add valid OPENAI_API_KEY
```

### Health Check Failing
```bash
# Manual health check
curl -v http://localhost:8888/docs

# Check container health status
docker inspect mem0_server --format='{{.State.Health.Status}}'
```

## Configuration Files

- **Environment:** `mem0.env`
- **Compose:** `docker-compose.yml`
- **Dockerfile:** `Dockerfile.mem0`
- **Data Volume:** `/Users/kermit/mem0-data/`

## Key Environment Variables

```bash
# Neo4j (shared intel-neo4j)
NEO4J_URI=bolt://intel-system-intel-neo4j-1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=intel123

# PostgreSQL (local mem0_postgres)
POSTGRES_HOST=postgres
POSTGRES_USER=mem0_user
POSTGRES_DB=mem0

# API
MEM0_PORT=8888
OPENAI_API_KEY=<your-key-here>
```

## Network Architecture

```
mem0_server:8888 ──┬─→ mem0_postgres:5432 (mem0_internal)
                   └─→ intel-neo4j:7687 (intel-system_intel-network)
```

## Success Indicators

✅ `docker compose ps` shows all services "Up (healthy)"
✅ `curl localhost:8888/docs` returns HTML
✅ No restart loops in `docker compose logs`
✅ PostgreSQL tables exist (mem0migrations, memories)
✅ Neo4j connection test succeeds

## Support

- **Fix Summary:** See `FIX_SUMMARY.md` for detailed troubleshooting
- **Logs Location:** Docker stdout (use `docker compose logs`)
- **Data Persistence:** `/Users/kermit/mem0-data/`

---
Last Updated: 2025-10-16
