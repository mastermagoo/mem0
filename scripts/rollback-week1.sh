#!/bin/bash
# Location: /Volumes/intel-system/deployment/docker/mem0_tailscale/rollback-week1.sh
# Purpose: Emergency rollback script for Week 1 mem0/tailscale fixes
# Scope: Restores .env and docker-compose.yml from backups, restarts services

set -e  # Exit on any error

echo "🔄 Rolling back Week 1 fixes..."
echo "=================================================="

# Change to mem0_tailscale directory
cd /Volumes/intel-system/deployment/docker/mem0_tailscale

# Find most recent backups (excluding literal $(date) filenames)
ENV_BACKUP=$(ls -t .env.backup-20* 2>/dev/null | head -1)
COMPOSE_BACKUP=$(ls -t docker-compose.yml.backup-20* 2>/dev/null | head -1)

# Validate backups exist
if [ -z "$ENV_BACKUP" ]; then
    echo "❌ No .env backup found!"
    echo "Available backups:"
    ls -lah .env.backup-* 2>/dev/null || echo "None found"
    exit 1
fi

if [ -z "$COMPOSE_BACKUP" ]; then
    echo "❌ No docker-compose.yml backup found!"
    echo "Available backups:"
    ls -lah docker-compose.yml.backup-* 2>/dev/null || echo "None found"
    exit 1
fi

echo "📋 Rollback Plan:"
echo "  .env: $ENV_BACKUP"
echo "  docker-compose.yml: $COMPOSE_BACKUP"
echo ""

# Create emergency backup of current state before rollback
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
echo "💾 Creating emergency backup of current state..."
cp .env ".env.pre-rollback-$TIMESTAMP"
cp docker-compose.yml "docker-compose.yml.pre-rollback-$TIMESTAMP"

# Stop services
echo "🛑 Stopping services..."
docker-compose down

# Restore backups
echo "📦 Restoring backups..."
cp "$ENV_BACKUP" .env
cp "$COMPOSE_BACKUP" docker-compose.yml

# Start services
echo "🚀 Starting services with restored configuration..."
docker-compose up -d

# Wait for services to initialize
echo "⏳ Waiting 30 seconds for services to initialize..."
sleep 30

# Check service status
echo "📊 Service Status:"
docker-compose ps

# Test health endpoints
echo ""
echo "🏥 Health Check:"
echo "  mem0: $(curl -s http://localhost:8001/health 2>/dev/null && echo '✅ OK' || echo '❌ FAIL')"
echo "  tailscale: $(docker-compose exec -T tailscale tailscale status --json 2>/dev/null | grep -q 'Online' && echo '✅ OK' || echo '❌ FAIL')"

echo ""
echo "=================================================="
echo "✅ Rollback complete"
echo ""
echo "📌 Backup locations:"
echo "  Original .env: $ENV_BACKUP"
echo "  Original compose: $COMPOSE_BACKUP"
echo "  Pre-rollback .env: .env.pre-rollback-$TIMESTAMP"
echo "  Pre-rollback compose: docker-compose.yml.pre-rollback-$TIMESTAMP"
echo ""
echo "💡 To verify:"
echo "  docker-compose logs -f mem0"
echo "  docker-compose logs -f tailscale"
