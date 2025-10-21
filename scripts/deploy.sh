#!/bin/bash
# Mem0 Platform Deployment Script

set -e

PROJECT_ROOT="/Volumes/Data/ai_projects/mem0-platform"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.prd}"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker/docker-compose.yml}"

echo "============================================"
echo "Mem0 Platform Deployment"
echo "============================================"
echo "Project: $PROJECT_ROOT"
echo "Environment: $ENV_FILE"
echo "Compose: $COMPOSE_FILE"
echo "============================================"
echo ""

# Check env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: Environment file not found: $ENV_FILE"
    echo ""
    echo "Create it from template:"
    echo "  cp $PROJECT_ROOT/.env.example $ENV_FILE"
    echo ""
    exit 1
fi

# Navigate to docker directory
cd "$PROJECT_ROOT/docker"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose --env-file "$ENV_FILE" down 2>/dev/null || true

# Pull latest images
echo ""
echo "📥 Pulling latest images..."
docker-compose --env-file "$ENV_FILE" pull

# Build custom images
echo ""
echo "🔨 Building custom images..."
docker-compose --env-file "$ENV_FILE" build

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose --env-file "$ENV_FILE" up -d

# Wait for services
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Show status
echo ""
echo "📊 Service Status:"
docker-compose --env-file "$ENV_FILE" ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "  - View logs: docker-compose --env-file $ENV_FILE logs -f"
echo "  - Check health: docker-compose --env-file $ENV_FILE ps"
echo "  - Access Mem0: http://localhost:8888/docs"
echo "  - Access Grafana: http://localhost:3001"
echo ""
