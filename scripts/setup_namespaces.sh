#!/bin/bash
# Namespace Setup Script
# Location: repo root (this repository)
# Purpose: Apply namespace isolation to PostgreSQL and Neo4j databases
# Usage: ./setup_namespaces.sh

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine environment and container names
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-}"
if [ -z "$DEPLOYMENT_ENV" ]; then
    echo -e "${RED}Error: DEPLOYMENT_ENV is required (test|prd)${NC}"
    exit 1
fi

case "$DEPLOYMENT_ENV" in
  prd|prod|production)
    ENV_SUFFIX="prd"
    ;;
  test)
    ENV_SUFFIX="test"
    ;;
  *)
    echo -e "${RED}Error: Unsupported DEPLOYMENT_ENV: $DEPLOYMENT_ENV (expected test|prd)${NC}"
    exit 1
    ;;
esac

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-mem0_postgres_${ENV_SUFFIX}}"
NEO4J_CONTAINER="${NEO4J_CONTAINER:-mem0_neo4j_${ENV_SUFFIX}}"
MEM0_CONTAINER="${MEM0_CONTAINER:-mem0_server_${ENV_SUFFIX}}"

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Namespace Isolation Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if containers are running
check_container() {
    local container=$1
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "${RED}Error: Container ${container} is not running${NC}"
        return 1
    fi
    return 0
}

echo -e "${YELLOW}Checking containers...${NC}"
check_container "$POSTGRES_CONTAINER" || exit 1
check_container "$NEO4J_CONTAINER" || exit 1
echo -e "${GREEN}✓ All containers running${NC}"
echo ""

# ================================================================================
# STEP 1: PostgreSQL Setup
# ================================================================================

echo -e "${YELLOW}Step 1: Setting up PostgreSQL namespace isolation...${NC}"

# Apply PostgreSQL schema
docker exec -i "$POSTGRES_CONTAINER" psql -U "${POSTGRES_USER:-mem0_user}" -d "${POSTGRES_DB:-mem0}" <<'EOF'
-- Add namespace column
ALTER TABLE memories
ADD COLUMN IF NOT EXISTS namespace VARCHAR(50) NOT NULL DEFAULT 'personal';

-- Add constraint
ALTER TABLE memories
DROP CONSTRAINT IF EXISTS chk_valid_namespace;

ALTER TABLE memories
ADD CONSTRAINT chk_valid_namespace
CHECK (namespace IN ('progressief', 'cv_automation', 'investments', 'personal', 'intel_system'));

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_memories_namespace_user
ON memories(namespace, user_id);

CREATE INDEX IF NOT EXISTS idx_memories_namespace_created
ON memories(namespace, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memories_namespace
ON memories(namespace);

-- Verify setup
SELECT
    'Namespace column exists' as check,
    COUNT(*) > 0 as passed
FROM information_schema.columns
WHERE table_name = 'memories'
  AND column_name = 'namespace';

EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PostgreSQL namespace isolation configured${NC}"
else
    echo -e "${RED}✗ PostgreSQL setup failed${NC}"
    exit 1
fi

echo ""

# ================================================================================
# STEP 2: Neo4j Setup
# ================================================================================

echo -e "${YELLOW}Step 2: Setting up Neo4j namespace isolation...${NC}"

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to be ready..."
sleep 5

# Apply Neo4j schema
docker exec -i "$NEO4J_CONTAINER" cypher-shell -u neo4j -p "${NEO4J_PASSWORD:?NEO4J_PASSWORD is required}" <<'EOF'
// Create constraints
CREATE CONSTRAINT mem_namespace_required IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.namespace IS NOT NULL;

CREATE CONSTRAINT mem_user_id_required IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.user_id IS NOT NULL;

CREATE CONSTRAINT mem_id_unique IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.id IS UNIQUE;

// Create indexes
CREATE INDEX mem_namespace_user IF NOT EXISTS
FOR (m:Memory)
ON (m.namespace, m.user_id);

CREATE INDEX mem_namespace_timestamp IF NOT EXISTS
FOR (m:Memory)
ON (m.namespace, m.created_at);

CREATE INDEX mem_user_only IF NOT EXISTS
FOR (m:Memory)
ON (m.user_id);
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Neo4j namespace isolation configured${NC}"
else
    echo -e "${RED}✗ Neo4j setup failed${NC}"
    exit 1
fi

echo ""

# ================================================================================
# STEP 3: Verify Setup
# ================================================================================

echo -e "${YELLOW}Step 3: Verifying namespace isolation...${NC}"

# Check PostgreSQL
echo "Checking PostgreSQL..."
POSTGRES_CHECK=$(docker exec "$POSTGRES_CONTAINER" psql -U "${POSTGRES_USER:-mem0_user}" -d "${POSTGRES_DB:-mem0}" -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'memories' AND column_name = 'namespace';")

if [ "${POSTGRES_CHECK// /}" = "1" ]; then
    echo -e "${GREEN}✓ PostgreSQL namespace column exists${NC}"
else
    echo -e "${RED}✗ PostgreSQL verification failed${NC}"
    exit 1
fi

# Check Neo4j
echo "Checking Neo4j..."
NEO4J_CHECK=$(docker exec "$NEO4J_CONTAINER" cypher-shell -u neo4j -p "${NEO4J_PASSWORD:?NEO4J_PASSWORD is required}" "SHOW CONSTRAINTS" 2>/dev/null | grep -c "mem_namespace_required" || echo "0")

if [ "$NEO4J_CHECK" -ge "1" ]; then
    echo -e "${GREEN}✓ Neo4j namespace constraints exist${NC}"
else
    echo -e "${RED}✗ Neo4j verification failed${NC}"
    exit 1
fi

echo ""

# ================================================================================
# STEP 4: Restart mem0 Server
# ================================================================================

echo -e "${YELLOW}Step 4: Restarting mem0 server...${NC}"

# Check if mem0_server is running
if docker ps --format '{{.Names}}' | grep -q "^${MEM0_CONTAINER}$"; then
    docker restart "$MEM0_CONTAINER"

    # Wait for health check
    echo "Waiting for mem0 server to be healthy..."
    for i in {1..30}; do
        if docker exec "$MEM0_CONTAINER" curl -sf http://localhost:8888/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ mem0 server restarted and healthy${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${YELLOW}⚠ mem0 server may not be fully ready yet${NC}"
        fi
        sleep 2
    done
else
    echo -e "${YELLOW}⚠ mem0_server is not running, skipping restart${NC}"
fi

echo ""

# ================================================================================
# STEP 5: Summary
# ================================================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Namespace isolation is now active!${NC}"
echo ""
echo "Available namespaces:"
echo "  1. progressief      - Business consulting"
echo "  2. cv_automation    - Job search"
echo "  3. investments      - Financial tracking"
echo "  4. personal         - Personal life (DEFAULT)"
echo "  5. intel_system     - Infrastructure"
echo ""
echo "Next steps:"
echo "  1. Read the user guide: NAMESPACE_GUIDE.md"
echo "  2. Test isolation: python test_namespace_isolation.py"
echo "  3. Start using: curl http://localhost:8888/v1/namespace/list"
echo ""
echo -e "${YELLOW}Important:${NC} All new memories default to 'personal' namespace"
echo -e "${YELLOW}Use X-Namespace header or /namespace commands to specify${NC}"
echo ""

# Show quick test command
echo -e "${BLUE}Quick test:${NC}"
echo "curl http://localhost:8888/v1/namespace/list"
echo ""
