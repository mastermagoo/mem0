#!/bin/bash
# Start mem0 TEST environment
# Usage: ./scripts/start_test.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_DIR"

# Load TEST environment variables
if [[ -f "$REPO_DIR/.env.test" ]]; then
  source "$REPO_DIR/.env.test"
fi

# Set TEST ports (non-conflicting with PRD)
export DEPLOYMENT_ENV=test
export POSTGRES_PORT="${POSTGRES_PORT:-15432}"
export NEO4J_HTTP_PORT="${NEO4J_HTTP_PORT:-17474}"
export NEO4J_BOLT_PORT="${NEO4J_BOLT_PORT:-17687}"
export GRAFANA_PORT="${GRAFANA_PORT:-13000}"
export MEM0_PORT="${MEM0_PORT:-18888}"

echo "🚀 Starting mem0 TEST environment..."
echo "   Ports: mem0=$MEM0_PORT, postgres=$POSTGRES_PORT, neo4j=$NEO4J_HTTP_PORT/$NEO4J_BOLT_PORT, grafana=$GRAFANA_PORT"

docker compose -f docker-compose.test.yml -p mem0-test up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

echo ""
echo "📊 TEST Environment Status:"
docker ps --filter "name=mem0.*test" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "✅ TEST environment started!"
echo "   API: http://localhost:$MEM0_PORT/docs"
