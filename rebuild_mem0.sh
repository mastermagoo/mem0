#!/bin/bash
#
# Rebuild mem0 Container from Scratch
# Location: /Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale/rebuild_mem0.sh
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo "mem0 Container Rebuild Script"
echo "================================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Verify required files exist
echo "📋 Step 1: Verifying required files..."
if [ ! -f "Dockerfile.mem0" ]; then
    echo -e "${RED}❌ Dockerfile.mem0 not found!${NC}"
    exit 1
fi

if [ ! -f "llm_router.py" ]; then
    echo -e "${RED}❌ llm_router.py not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required files present${NC}"
echo ""

# Step 2: Stop existing container (if running)
echo "🛑 Step 2: Stopping existing mem0 container..."
if docker ps -a --format '{{.Names}}' | grep -q "^mem0_server_prd$"; then
    docker stop mem0_server_prd 2>/dev/null || true
    echo -e "${YELLOW}⚠️  Stopped existing container${NC}"
else
    echo -e "${GREEN}✅ No existing container to stop${NC}"
fi
echo ""

# Step 3: Remove old image (optional - keeps last version as backup)
echo "🗑️  Step 3: Managing old images..."
if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^mem0-fixed:local$"; then
    # Tag old version as backup
    docker tag mem0-fixed:local mem0-fixed:backup-$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    echo -e "${YELLOW}⚠️  Tagged old image as backup${NC}"
fi
echo ""

# Step 4: Build new image
echo "🔨 Step 4: Building new mem0-fixed:local image..."
echo "This may take 2-5 minutes depending on network speed..."
echo ""

docker build -f Dockerfile.mem0 -t mem0-fixed:local .

echo ""
echo -e "${GREEN}✅ Build completed successfully${NC}"
echo ""

# Step 5: Verify build
echo "🔍 Step 5: Verifying new image..."
if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^mem0-fixed:local$"; then
    IMAGE_SIZE=$(docker images mem0-fixed:local --format "{{.Size}}")
    IMAGE_ID=$(docker images mem0-fixed:local --format "{{.ID}}")
    echo -e "${GREEN}✅ Image verified:${NC}"
    echo "   - Image ID: $IMAGE_ID"
    echo "   - Size: $IMAGE_SIZE"
else
    echo -e "${RED}❌ Image verification failed!${NC}"
    exit 1
fi
echo ""

# Step 6: Instructions for redeployment
echo "================================================================================"
echo -e "${GREEN}✅ REBUILD COMPLETE${NC}"
echo "================================================================================"
echo ""
echo "Next steps to deploy the new image:"
echo ""
echo "1. Start the container:"
echo "   cd /Volumes/Data/ai_projects/intel-system/deployment/docker/mem0_tailscale"
echo "   docker-compose -f docker-compose.prd.yml up -d mem0"
echo ""
echo "2. Verify it's running:"
echo "   docker ps --filter 'name=mem0_server_prd'"
echo ""
echo "3. Check health:"
echo "   curl http://localhost:8888/health"
echo ""
echo "4. Test API:"
echo "   curl http://localhost:8888/memories?user_id=test"
echo ""
echo "================================================================================"
echo ""
echo "📦 Image Details:"
echo "   Repository: mem0-fixed"
echo "   Tag: local"
echo "   Base: mem0/mem0-api-server:latest"
echo "   Custom: PostgreSQL + Neo4j + LLM routing"
echo "   API Path: /memories (correct ✅)"
echo ""
echo "================================================================================"
