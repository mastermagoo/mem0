# mem0 Troubleshooting Guide

**Version**: 2.0 (Local Neo4j with GDS Plugin)  
**Date**: 2025-10-21  
**Architecture**: Self-Contained, Zero Dependencies

## 🚨 Common Issues & Solutions

### Issue 1: Container Won't Start

#### Symptoms
- Container shows "Restarting" or "Exited" status
- Services fail to start during `docker compose up -d`

#### Diagnosis
```bash
# Check container status
cd /Volumes/intel-system/deployment/docker/mem0_tailscale
docker compose --env-file mem0.env ps

# Check logs for specific service
docker compose --env-file mem0.env logs mem0_prd
docker compose --env-file mem0.env logs mem0_neo4j_prd
docker compose --env-file mem0.env logs mem0_postgres_prd
```

#### Solutions

**Port Conflicts:**
```bash
# Check for port conflicts
lsof -i :8888  # mem0 API
lsof -i :5433  # PostgreSQL
lsof -i :7475  # Neo4j HTTP
lsof -i :7688  # Neo4j Bolt
lsof -i :3001  # Grafana

# Kill conflicting processes
sudo kill -9 [PID]
```

**Permission Issues:**
```bash
# Fix data directory permissions
sudo chown -R $(whoami):staff /Users/kermit/mem0-data/
chmod -R 755 /Users/kermit/mem0-data/
```

**Resource Constraints:**
```bash
# Check Docker resources
docker system df
docker system prune -f

# Check system resources
top
df -h
```

### Issue 2: Neo4j Connection Problems

#### Symptoms
- mem0_prd container shows "Cannot resolve address" errors
- Neo4j GDS functions not available
- Memory creation fails with Neo4j errors

#### Diagnosis
```bash
# Test Neo4j connectivity
docker exec mem0_neo4j_prd cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "CALL gds.version()"

# Check Neo4j logs
docker compose --env-file mem0.env logs mem0_neo4j_prd

# Test network connectivity
docker exec mem0_prd ping neo4j
```

#### Solutions

**GDS Plugin Issues:**
```bash
# Restart Neo4j with clean data
docker compose --env-file mem0.env stop mem0_neo4j_prd
rm -rf /Users/kermit/mem0-data/neo4j
docker compose --env-file mem0.env up -d mem0_neo4j_prd

# Wait for Neo4j to be healthy
docker compose --env-file mem0.env logs -f mem0_neo4j_prd
```

**Network Issues:**
```bash
# Recreate network
docker compose --env-file mem0.env down
docker network prune -f
docker compose --env-file mem0.env up -d
```

### Issue 3: Memory Creation Failures

#### Symptoms
- API returns 500 errors
- Memory creation requests fail
- No memories stored in database

#### Diagnosis
```bash
# Check mem0 logs
docker compose --env-file mem0.env logs mem0_prd | grep -i error

# Test API directly
curl -X POST http://localhost:8888/memories \
  -H 'Content-Type: application/json' \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d' \
  -d '{"messages": [{"role": "user", "content": "test"}], "user_id": "test"}'

# Check database connectivity
docker exec mem0_postgres_prd psql -U mem0_user -d mem0 -c "SELECT COUNT(*) FROM memories;"
```

#### Solutions

**Database Connection Issues:**
```bash
# Restart PostgreSQL
docker compose --env-file mem0.env restart mem0_postgres_prd

# Check PostgreSQL logs
docker compose --env-file mem0.env logs mem0_postgres_prd
```

**API Key Issues:**
```bash
# Verify API key in environment
docker exec mem0_prd env | grep MEM0_API_KEY

# Update API key if needed
# Edit mem0.env file and restart
docker compose --env-file mem0.env restart mem0_prd
```

### Issue 4: Performance Problems

#### Symptoms
- Slow memory creation
- High CPU/memory usage
- Timeout errors

#### Diagnosis
```bash
# Check resource usage
docker stats

# Check service health
docker compose --env-file mem0.env ps

# Monitor logs for performance issues
docker compose --env-file mem0.env logs mem0_prd | grep -i "slow\|timeout\|error"
```

#### Solutions

**Resource Optimization:**
```bash
# Increase Docker resources in Docker Desktop
# Or optimize container resource limits in docker-compose.yml

# Clean up unused resources
docker system prune -f
docker volume prune -f
```

**Database Optimization:**
```bash
# Optimize PostgreSQL
docker exec mem0_postgres_prd psql -U mem0_user -d mem0 -c "VACUUM ANALYZE;"

# Optimize Neo4j
docker exec mem0_neo4j_prd cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "CALL apoc.periodic.commit('MATCH (n) RETURN count(n) LIMIT 1000', 'MATCH (n) WITH n LIMIT 1000 DETACH DELETE n RETURN count(n)');"
```

### Issue 5: Grafana Access Problems

#### Symptoms
- Cannot access Grafana at http://localhost:3001
- Login fails
- Dashboards not loading

#### Diagnosis
```bash
# Check Grafana container status
docker compose --env-file mem0.env ps mem0_grafana_prd

# Check Grafana logs
docker compose --env-file mem0.env logs mem0_grafana_prd

# Test port accessibility
curl http://localhost:3001
```

#### Solutions

**Port Issues:**
```bash
# Check port binding
docker port mem0_grafana_prd

# Restart Grafana
docker compose --env-file mem0.env restart mem0_grafana_prd
```

**Authentication Issues:**
```bash
# Reset Grafana admin password
docker exec mem0_grafana_prd grafana-cli admin reset-admin-password \"$GRAFANA_PASSWORD\"
```

### Issue 6: Telegram Bot Problems

#### Symptoms
- Telegram bot not responding
- Bot commands fail
- Connection errors

#### Diagnosis
```bash
# Check bot container status
docker compose --env-file mem0.env ps mem0_telegram_bot_prd

# Check bot logs
docker compose --env-file mem0.env logs mem0_telegram_bot_prd

# Verify bot token
docker exec mem0_telegram_bot_prd env | grep TELEGRAM_BOT_TOKEN
```

#### Solutions

**Token Issues:**
```bash
# Update bot token in mem0.env
# Restart bot container
docker compose --env-file mem0.env restart mem0_telegram_bot_prd
```

**Network Issues:**
```bash
# Check bot connectivity to mem0 API
docker exec mem0_telegram_bot_prd curl http://mem0_prd:8888/health
```

## 🔍 Diagnostic Commands

### System Health Check
```bash
#!/bin/bash
# Complete system health check

echo "=== mem0 System Health Check ==="
echo "Date: $(date)"
echo

echo "=== Container Status ==="
cd /Volumes/intel-system/deployment/docker/mem0_tailscale
docker compose --env-file mem0.env ps

echo
echo "=== Service Health ==="
echo "mem0 API:"
curl -s http://localhost:8888/health | jq .

echo "Neo4j GDS:"
docker exec mem0_neo4j_prd cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "CALL gds.version()" 2>/dev/null || echo "Neo4j GDS not available"

echo "PostgreSQL:"
docker exec mem0_postgres_prd psql -U mem0_user -d mem0 -c "SELECT version();" 2>/dev/null || echo "PostgreSQL not available"

echo
echo "=== Resource Usage ==="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo
echo "=== Network Status ==="
docker network inspect mem0_internal --format "{{.Containers}}" | wc -l
echo "Containers on mem0_internal network: $(docker network inspect mem0_internal --format '{{len .Containers}}')"

echo
echo "=== Data Directory ==="
ls -la /Users/kermit/mem0-data/
du -sh /Users/kermit/mem0-data/*

echo
echo "=== Recent Logs ==="
echo "mem0 API (last 5 lines):"
docker compose --env-file mem0.env logs mem0_prd --tail 5

echo "Neo4j (last 5 lines):"
docker compose --env-file mem0.env logs mem0_neo4j_prd --tail 5
```

### Memory Test
```bash
#!/bin/bash
# Test memory creation and retrieval

echo "=== Memory Creation Test ==="

# Test memory creation
echo "Creating test memory..."
RESPONSE=$(curl -s -X POST http://localhost:8888/memories \
  -H 'Content-Type: application/json' \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d' \
  -d '{"messages": [{"role": "user", "content": "Test memory creation at $(date)"}], "user_id": "test_user"}')

echo "Response: $RESPONSE"

# Test memory retrieval
echo "Retrieving test memories..."
curl -s "http://localhost:8888/memories?user_id=test_user" \
  -H 'MEM0_API_KEY: mem0-b0539021-c9a6-4aaa-9193-665f63851a0d' | jq .

echo "=== Memory Test Complete ==="
```

## 📊 Log Analysis

### Common Log Patterns

**Neo4j GDS Patch Success:**
```
✅ Neo4jGraph.query() patched successfully
   - vector.similarity.cosine → gds.similarity.cosine
   - vector.similarity.euclidean → gds.similarity.euclidean
```

**Memory Creation Success:**
```
INFO:     192.168.97.1:53994 - "POST /memories HTTP/1.1" 200 OK
```

**Database Connection Success:**
```
INFO - Total existing memories: 0
INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
```

**Error Patterns:**
```
ERROR - Cannot resolve address neo4j:7687
ERROR - Connection refused to postgres:5432
ERROR - API key validation failed
```

### Log Monitoring
```bash
# Monitor all logs in real-time
docker compose --env-file mem0.env logs -f

# Monitor specific service
docker compose --env-file mem0.env logs -f mem0_prd

# Filter for errors only
docker compose --env-file mem0.env logs mem0_prd | grep -i error

# Filter for specific patterns
docker compose --env-file mem0.env logs mem0_prd | grep -i "memory\|neo4j\|postgres"
```

## 🔧 Recovery Procedures

### Complete System Reset
```bash
#!/bin/bash
# Complete system reset (WARNING: This deletes all data)

echo "WARNING: This will delete all mem0 data!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo "Stopping all services..."
    cd /Volumes/intel-system/deployment/docker/mem0_tailscale
    docker compose --env-file mem0.env down -v
    
    echo "Removing data directories..."
    rm -rf /Users/kermit/mem0-data/
    
    echo "Cleaning up Docker resources..."
    docker system prune -f
    docker volume prune -f
    docker network prune -f
    
    echo "Starting fresh deployment..."
    docker compose --env-file mem0.env up -d
    
    echo "System reset complete!"
else
    echo "Reset cancelled."
fi
```

### Data Recovery
```bash
#!/bin/bash
# Restore from backup

BACKUP_DATE=$1
if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    ls -la /Users/kermit/mem0-data/backups/
    exit 1
fi

echo "Restoring from backup: $BACKUP_DATE"

# Stop services
cd /Volumes/intel-system/deployment/docker/mem0_tailscale
docker compose --env-file mem0.env down

# Restore PostgreSQL
echo "Restoring PostgreSQL..."
gunzip < /Users/kermit/mem0-data/backups/$BACKUP_DATE/postgres/mem0_${BACKUP_DATE}.sql.gz | \
docker exec -i mem0_postgres_prd psql -U mem0_user -d mem0

# Restore Neo4j
echo "Restoring Neo4j..."
tar -xzf /Users/kermit/mem0-data/backups/$BACKUP_DATE/neo4j/mem0_neo4j_${BACKUP_DATE}.tar.gz \
    -C /Users/kermit/mem0-data/neo4j/

# Start services
docker compose --env-file mem0.env up -d

echo "Restore complete!"
```

## 📞 Support Information

### Before Contacting Support
1. Run the system health check script
2. Check logs for error patterns
3. Verify all prerequisites are met
4. Test individual components

### Information to Provide
- System health check output
- Relevant log excerpts
- Steps to reproduce the issue
- Expected vs actual behavior

### Emergency Contacts
- **System**: mem0 Personal AI Memory
- **Environment**: PRD (Production)
- **Architecture**: Self-contained, zero dependencies

---

**✅ mem0 Troubleshooting Guide**  
**Last Updated**: 2025-10-21  
**Version**: 2.0 (Local Neo4j with GDS Plugin)
