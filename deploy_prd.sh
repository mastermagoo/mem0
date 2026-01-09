#!/bin/bash
#
# Production Deployment Script for mem0
# Location: repo root (this repository)
#
# MANDATORY: This script MUST be used for all production deployments
# FORBIDDEN: Direct docker-compose commands in production
#
# Usage:
#   ./deploy_prd.sh [up|down|restart|status|logs]
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prd.yml"
ENV_FILE=".env"
REQUIRED_ENV_VAR="DEPLOYMENT_ENV"
REQUIRED_ENV_VALUE="prd"

echo "================================================================================"
echo "🚀 mem0 Production Deployment Script"
echo "================================================================================"
echo ""

# Function: Print colored message
print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function: Validate environment
validate_environment() {
    print_info "Validating production environment..."

    # Check compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    # Check .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file not found: $ENV_FILE"
        print_info "Production deployments require $ENV_FILE file"
        exit 1
    fi

    # Check DEPLOYMENT_ENV is set to 'prd'
    if ! grep -q "^DEPLOYMENT_ENV=prd" "$ENV_FILE"; then
        print_error "DEPLOYMENT_ENV must be set to 'prd' in $ENV_FILE"
        print_info "Add this line to $ENV_FILE:"
        print_info "  DEPLOYMENT_ENV=prd"
        exit 1
    fi

    # Check required credentials present
    # NOTE:
    # - OPENAI_API_KEY is optional in Ollama-only mode.
    # - TELEGRAM_BOT_TOKEN is only required if you enable the `telegram` profile.
    local required_vars=("POSTGRES_PASSWORD" "NEO4J_PASSWORD" "MEM0_API_KEY" "GRAFANA_PASSWORD")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE"; then
            print_error "Required variable not found in $ENV_FILE: $var"
            exit 1
        fi
    done

    if ! grep -q "^TELEGRAM_BOT_TOKEN=" "$ENV_FILE"; then
        print_warning "TELEGRAM_BOT_TOKEN not set in $ENV_FILE (telegram bot profile will not work)"
    fi

    print_success "Environment validation passed"
}

# Function: Check if containers are running
check_status() {
    print_info "Checking container status..."
    docker ps --filter "label=com.intel-system.environment=production" \
              --filter "name=mem0" \
              --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
}

# Function: Deploy services
deploy_up() {
    validate_environment

    print_info "Deploying mem0 production stack..."
    print_warning "This will affect: intel-sys, wingman, cv-automation, accounting"

    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    echo ""
    print_success "Deployment initiated"
    print_info "Waiting 10 seconds for services to start..."
    sleep 10

    check_status

    echo ""
    print_info "Verifying health endpoints..."
    sleep 5

    if curl -fsS http://localhost:8888/health > /dev/null 2>&1; then
        print_success "mem0 API is healthy"
    else
        print_warning "mem0 API not responding yet (may need more time)"
    fi
}

# Function: Stop services
deploy_down() {
    print_warning "Stopping mem0 production stack..."
    print_warning "This will affect: intel-sys, wingman, cv-automation, accounting"

    docker compose -f "$COMPOSE_FILE" down

    print_success "Services stopped"
}

# Function: Restart services
deploy_restart() {
    validate_environment

    print_info "Restarting mem0 production stack..."

    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart

    echo ""
    print_success "Services restarted"
    sleep 5
    check_status
}

# Function: Show logs
show_logs() {
    local service="${2:-}"

    if [ -z "$service" ]; then
        print_info "Showing logs for all services (last 50 lines)..."
        docker compose -f "$COMPOSE_FILE" logs --tail=50
    else
        print_info "Showing logs for $service (last 50 lines)..."
        docker compose -f "$COMPOSE_FILE" logs --tail=50 "$service"
    fi
}

# Function: Validate deployment
validate_deployment() {
    print_info "Validating production deployment..."

    local errors=0

    # Check all expected containers exist
    local expected_containers=("mem0_postgres_prd" "mem0_server_prd" "mem0_grafana_prd")
    for container in "${expected_containers[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            print_success "$container is running"
        else
            print_error "$container is NOT running"
            ((errors++))
        fi
    done

    # Check containers have correct labels
    local label_count=$(docker ps --filter "label=com.intel-system.compose-file=docker-compose.prd.yml" | wc -l)
    if [ "$label_count" -gt 1 ]; then
        print_success "Containers have correct deployment labels"
    else
        print_error "Containers missing deployment labels"
        ((errors++))
    fi

    # Check network
    if docker network inspect mem0_internal > /dev/null 2>&1; then
        print_success "Network mem0_internal exists"

        local network_containers=$(docker network inspect mem0_internal --format '{{range .Containers}}{{.Name}} {{end}}')
        print_info "Containers on network: $network_containers"
    else
        print_error "Network mem0_internal does not exist"
        ((errors++))
    fi

    # Check API health
    if curl -fsS http://localhost:8888/health > /dev/null 2>&1; then
        print_success "mem0 API health check passed"
    else
        print_warning "mem0 API health check failed (may need more startup time)"
    fi

    echo ""
    if [ $errors -eq 0 ]; then
        print_success "✅ PRODUCTION DEPLOYMENT VALIDATED"
        return 0
    else
        print_error "❌ PRODUCTION DEPLOYMENT HAS $errors ERROR(S)"
        return 1
    fi
}

# Main script logic
ACTION="${1:-status}"

case "$ACTION" in
    up|start)
        deploy_up
        echo ""
        validate_deployment
        ;;
    down|stop)
        deploy_down
        ;;
    restart)
        deploy_restart
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs "$@"
        ;;
    validate)
        validate_deployment
        ;;
    *)
        echo "Usage: $0 {up|down|restart|status|logs|validate} [service]"
        echo ""
        echo "Commands:"
        echo "  up        - Deploy/start all services"
        echo "  down      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show container status"
        echo "  logs      - Show logs (optionally for specific service)"
        echo "  validate  - Validate deployment configuration"
        echo ""
        echo "Examples:"
        echo "  $0 up                    # Start all services"
        echo "  $0 logs mem0             # Show mem0 logs"
        echo "  $0 validate              # Validate deployment"
        exit 1
        ;;
esac

exit 0
