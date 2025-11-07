# mem0 Container Rebuild Guide

**Location**: `/Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale/`
**Last Updated**: 2025-10-30
**Status**: Production-ready ✅

---

## 🎯 Purpose

This guide documents the complete process for rebuilding the mem0 container from scratch, ensuring it uses the correct API paths (`/memories`) and includes all custom enhancements (PostgreSQL, Neo4j, LLM routing).

---

## 📋 Prerequisites

### Required Files
All files located in `/Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale/`:

- ✅ `Dockerfile.mem0` - Custom build configuration
- ✅ `llm_router.py` - LLM routing logic (19KB)
- ✅ `docker-compose.prd.yml` - Production compose file
- ✅ `rebuild_mem0.sh` - Automated rebuild script

### System Requirements
- Docker Desktop installed
- 2GB free disk space for image
- Network access to pull base image

---

## 🚀 Quick Rebuild (Automated)

### Option 1: Use the Rebuild Script (Recommended)

```bash
cd /Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale
./rebuild_mem0.sh
```

**What the script does**:
1. ✅ Verifies required files exist
2. ✅ Stops existing container (if running)
3. ✅ Tags old image as backup
4. ✅ Builds new `mem0-fixed:local` image
5. ✅ Verifies build success
6. ✅ Provides deployment instructions

**Duration**: 2-5 minutes (network dependent)

---

## 🔧 Manual Rebuild (Step-by-Step)

### Step 1: Navigate to Directory
```bash
cd /Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale
```

### Step 2: Verify Required Files
```bash
ls -lh Dockerfile.mem0 llm_router.py
```

Expected output:
```
-rwx------  1 kermit  staff  815B  Dockerfile.mem0
-rwx------  1 kermit  staff  19KB  llm_router.py
```

### Step 3: Build the Image
```bash
docker build -f Dockerfile.mem0 -t mem0-fixed:local .
```

**Build process** (~2-5 minutes):
```
[+] Building 60.0s
 => [1/5] FROM mem0/mem0-api-server:latest
 => [2/5] RUN apt-get update && apt-get install -y libpq-dev gcc curl
 => [3/5] RUN pip install psycopg2-binary psycopg langchain-neo4j rank-bm25...
 => [4/5] COPY llm_router.py /app/llm_router.py
 => [5/5] RUN python -c "import psycopg2; print('PostgreSQL drivers OK')"
 => exporting to image
 => => naming to docker.io/library/mem0-fixed:local
```

### Step 4: Verify Build
```bash
docker images | grep mem0-fixed
```

Expected output:
```
mem0-fixed   local   <image_id>   X minutes ago   736MB
```

### Step 5: Test the Image (Optional)
```bash
# Start a test container
docker run --rm -d --name mem0_test \
  -p 8889:8888 \
  -e DATABASE_URL="postgresql://test:test@localhost/test" \
  -e OPENAI_API_KEY="test-key" \
  -e MEM0_API_KEY="test-key" \
  mem0-fixed:local

# Wait 10 seconds for startup
sleep 10

# Check API documentation
curl http://localhost:8889/docs

# Stop test container
docker stop mem0_test
```

---

## 🔄 Deployment After Rebuild

### Option 1: Recreate Container (Recommended)
```bash
cd /Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale

# Stop and remove old container
docker-compose -f docker-compose.prd.yml down mem0

# Start with new image
docker-compose -f docker-compose.prd.yml up -d mem0
```

### Option 2: Full Stack Restart
```bash
# Stop all services
docker-compose -f docker-compose.prd.yml down

# Start all services with new image
docker-compose -f docker-compose.prd.yml up -d
```

### Verify Deployment
```bash
# Check container status
docker ps --filter "name=mem0_server_prd"

# Check logs
docker logs mem0_server_prd --tail 50

# Test health endpoint
curl http://localhost:8888/health

# Test memories API (correct path ✅)
curl -X POST http://localhost:8888/memories \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"user_id":"rebuild_test"}'
```

---

## 📦 What's Included in the Custom Image

### Base Image
- **Source**: `mem0/mem0-api-server:latest`
- **Official mem0 platform**: FastAPI + core memory features

### Custom Additions

#### 1. PostgreSQL Support
```dockerfile
RUN apt-get install -y libpq-dev gcc
RUN pip install psycopg2-binary psycopg[binary,pool]
```
- **Why**: Better PostgreSQL performance than SQLite
- **Benefit**: Production-ready database support

#### 2. Neo4j Graph Database
```dockerfile
RUN pip install langchain-neo4j
```
- **Why**: Enhanced relationship mapping
- **Benefit**: Complex memory connections and graph queries

#### 3. BM25 Search Ranking
```dockerfile
RUN pip install rank-bm25
```
- **Why**: Better semantic search
- **Benefit**: Improved memory retrieval accuracy

#### 4. LLM Routing
```dockerfile
COPY llm_router.py /app/llm_router.py
```
- **Why**: Local-first LLM strategy (Ollama → OpenAI fallback)
- **Benefit**: Cost optimization ($0 for most requests)

#### 5. Enhanced Server
```dockerfile
RUN pip install uvicorn[standard] httpx openai
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888"]
```
- **Why**: Production-grade ASGI server
- **Benefit**: Better performance and async support

---

## 🔍 Verification Checklist

After rebuild and deployment, verify:

- [ ] Container is running: `docker ps --filter "name=mem0_server_prd"`
- [ ] Health check passes: `curl http://localhost:8888/health`
- [ ] API docs accessible: `curl http://localhost:8888/docs`
- [ ] Correct API path: `/memories` (not `/v1/memories`)
- [ ] PostgreSQL connected: Check logs for DB connection
- [ ] Neo4j connected: Check logs for graph connection (if applicable)
- [ ] Memory creation works: Test POST to `/memories`
- [ ] Memory retrieval works: Test GET from `/memories?user_id=test`

---

## 🐛 Troubleshooting

### Issue 1: Build Fails - Missing llm_router.py
```bash
Error: COPY failed: file not found: llm_router.py
```

**Solution**:
```bash
# Verify file exists
ls -la /Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale/llm_router.py

# Re-run build from correct directory
cd /Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale
docker build -f Dockerfile.mem0 -t mem0-fixed:local .
```

### Issue 2: Container Won't Start After Rebuild
```bash
Error: container exits immediately
```

**Solution**:
```bash
# Check logs
docker logs mem0_server_prd

# Common causes:
# 1. Missing environment variables
# 2. Database connection failed
# 3. Port already in use

# Fix: Check docker-compose.prd.yml environment section
```

### Issue 3: Old Image Still Being Used
```bash
Warning: container running old version
```

**Solution**:
```bash
# Force recreation
docker-compose -f docker-compose.prd.yml up -d --force-recreate mem0

# Or remove and recreate
docker stop mem0_server_prd
docker rm mem0_server_prd
docker-compose -f docker-compose.prd.yml up -d mem0
```

### Issue 4: API Returns Wrong Paths
```bash
Error: API uses /v1/memories instead of /memories
```

**Solution**:
This should NOT happen with the custom build. If it does:
```bash
# Verify correct image is running
docker inspect mem0_server_prd --format '{{.Config.Image}}'
# Should output: mem0-fixed:local

# If not, rebuild and redeploy
./rebuild_mem0.sh
docker-compose -f docker-compose.prd.yml up -d --force-recreate mem0
```

---

## 📚 Related Documentation

- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **API Reference**: `API_REFERENCE.md`
- **LLM Routing**: `LLM_ROUTING.md`
- **Namespace Architecture**: `NAMESPACE_ARCHITECTURE.md`

---

## 🔐 Security Notes

### Credentials in Build
- ❌ **DO NOT** hardcode credentials in Dockerfile
- ✅ **USE** environment variables at runtime
- ✅ **VERIFY** .env files are in .gitignore

### Image Distribution
- ⚠️ Custom image contains `llm_router.py` logic
- ⚠️ Tag images appropriately: `mem0-fixed:local` (not `latest`)
- ✅ Keep backup images: `mem0-fixed:backup-YYYYMMDD_HHMMSS`

---

## 💾 Backup Before Rebuild

**Recommended before major rebuilds**:

```bash
# 1. Tag current working image as backup
docker tag mem0-fixed:local mem0-fixed:backup-working

# 2. Export current image (optional - 736MB file)
docker save mem0-fixed:local -o mem0-fixed-backup.tar

# 3. Backup configuration
cp docker-compose.prd.yml docker-compose.prd.yml.backup

# 4. Document current version
docker inspect mem0-fixed:local | jq '.[0].Created' > image-version.txt
```

**Restore from backup**:
```bash
# If new build fails, restore old image
docker tag mem0-fixed:backup-working mem0-fixed:local
docker-compose -f docker-compose.prd.yml up -d --force-recreate mem0
```

---

## ✅ Success Criteria

A successful rebuild means:

1. ✅ Build completes without errors
2. ✅ Image size ~736MB (±50MB acceptable)
3. ✅ Container starts and becomes healthy
4. ✅ API responds on port 8888
5. ✅ `/memories` endpoint works (POST + GET)
6. ✅ PostgreSQL connection established
7. ✅ No hardcoded credentials in image
8. ✅ All custom modules (psycopg2, neo4j) import successfully

---

## 🔄 Update Frequency

**When to rebuild**:
- ✅ After changes to `Dockerfile.mem0`
- ✅ After updates to `llm_router.py`
- ✅ When mem0 releases major version (test first!)
- ✅ After security patches to base image

**When NOT to rebuild**:
- ❌ For environment variable changes (use docker-compose)
- ❌ For configuration changes (use volumes)
- ❌ For credential rotation (use .env files)

---

## 📞 Support

For issues with rebuild process:
1. Check this guide's troubleshooting section
2. Review Docker logs: `docker logs mem0_server_prd`
3. Verify all prerequisites are met
4. Test with clean Docker environment: `docker system prune -a` (WARNING: removes all unused images)

---

**End of Rebuild Guide**
