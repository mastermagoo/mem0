#!/bin/bash
# Location: /Volumes/intel-system/deployment/docker/mem0_tailscale/rotate-openai-key.sh
# Purpose: Automated OpenAI API key rotation for mem0_tailscale deployment
# Scope: Updates .env, verifies key, restarts services with rollback capability

set -euo pipefail

# Color output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
BACKUP_DIR="${SCRIPT_DIR}/.backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/.env.backup-${TIMESTAMP}"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help message
show_help() {
    cat <<EOF
OpenAI API Key Rotation Script for mem0_tailscale

USAGE:
    $0 <new-api-key> [options]

ARGUMENTS:
    new-api-key         The new OpenAI API key (sk-proj-...)

OPTIONS:
    --dry-run           Validate key format without making changes
    --skip-verify       Skip API key verification (not recommended)
    --no-restart        Update .env but don't restart services
    --help              Show this help message

EXAMPLES:
    # Standard rotation (recommended)
    $0 sk-proj-xxxxxxxxxxxxx

    # Dry run to validate key format
    $0 sk-proj-xxxxxxxxxxxxx --dry-run

    # Update without restarting (manual restart required)
    $0 sk-proj-xxxxxxxxxxxxx --no-restart

SAFETY FEATURES:
    - Automatic backup of current .env
    - Key format validation
    - API key verification before committing
    - Automatic rollback on failure
    - Service health checks after restart

PREREQUISITES:
    1. New API key from platform.openai.com
    2. Docker and docker-compose installed
    3. Sufficient permissions to modify .env and restart services
    4. curl installed for API verification

For detailed instructions, see:
    See docs/archive/ for key rotation guides
EOF
    exit 0
}

# Validate prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if running from correct directory
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env file not found at: $ENV_FILE"
        log_error "Please run this script from the mem0_tailscale directory"
        exit 1
    fi

    # Check if docker-compose file exists
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "docker-compose.yml not found at: $COMPOSE_FILE"
        exit 1
    fi

    # Check if docker is running
    if ! docker info &>/dev/null; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Check if curl is installed (for API verification)
    if ! command -v curl &>/dev/null; then
        log_warning "curl not found. API verification will be skipped."
        SKIP_VERIFY=true
    fi

    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"

    log_success "Prerequisites check passed"
}

# Validate API key format
validate_key_format() {
    local key=$1

    log_info "Validating API key format..."

    # Check if key starts with sk-proj- (new format) or sk- (legacy format)
    if [[ ! "$key" =~ ^sk-(proj-)?[A-Za-z0-9_-]{40,}$ ]]; then
        log_error "Invalid OpenAI API key format"
        log_error "Expected format: sk-proj-... or sk-..."
        log_error "Key length: minimum 43 characters"
        return 1
    fi

    # Check key length (without displaying the key)
    local key_length=${#key}
    log_success "Key format valid (${key_length} characters)"
    return 0
}

# Verify API key works by making test request
verify_api_key() {
    local key=$1

    if [[ "$SKIP_VERIFY" == true ]]; then
        log_warning "Skipping API key verification (--skip-verify flag set)"
        return 0
    fi

    log_info "Verifying API key with OpenAI API..."

    # Make a minimal API request to verify the key
    local response
    response=$(curl -s -w "\n%{http_code}" https://api.openai.com/v1/models \
        -H "Authorization: Bearer $key" 2>&1)

    local http_code=$(echo "$response" | tail -n1)

    if [[ "$http_code" == "200" ]]; then
        log_success "API key verification successful"
        return 0
    else
        log_error "API key verification failed (HTTP $http_code)"
        log_error "Please check that the key is valid and active"
        return 1
    fi
}

# Backup current .env file
backup_env_file() {
    log_info "Backing up current .env file..."

    if cp "$ENV_FILE" "$BACKUP_FILE"; then
        # Set restrictive permissions on backup
        chmod 600 "$BACKUP_FILE"
        log_success "Backup created: $BACKUP_FILE"

        # Check current key length (for comparison, not display)
        if grep -q "OPENAI_API_KEY" "$ENV_FILE"; then
            local current_key_length=$(grep "OPENAI_API_KEY" "$ENV_FILE" | cut -d'=' -f2 | wc -c | tr -d ' ')
            log_info "Current key length: $((current_key_length - 1)) characters"
        fi

        return 0
    else
        log_error "Failed to create backup"
        return 1
    fi
}

# Update .env file with new key
update_env_file() {
    local new_key=$1

    log_info "Updating .env file with new API key..."

    # Check if OPENAI_API_KEY exists in .env
    if ! grep -q "^OPENAI_API_KEY=" "$ENV_FILE"; then
        log_error "OPENAI_API_KEY not found in .env file"
        return 1
    fi

    # Use sed to replace the key (macOS compatible)
    if sed -i.tmp "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$new_key|" "$ENV_FILE"; then
        rm -f "${ENV_FILE}.tmp"

        # Update the timestamp comment
        local current_date=$(date '+%Y-%m-%d %H:%M:%S')
        sed -i.tmp "s|^# OpenAI Configuration.*|# OpenAI Configuration - Updated $current_date by rotate-openai-key.sh|" "$ENV_FILE"
        rm -f "${ENV_FILE}.tmp"

        # Verify the update (check length only)
        local new_key_length=$(grep "OPENAI_API_KEY" "$ENV_FILE" | cut -d'=' -f2 | wc -c | tr -d ' ')
        log_success ".env file updated successfully"
        log_info "New key length: $((new_key_length - 1)) characters"

        return 0
    else
        log_error "Failed to update .env file"
        return 1
    fi
}

# Restart mem0 services
restart_services() {
    log_info "Restarting mem0 services to apply new API key..."

    # Change to script directory for docker-compose
    cd "$SCRIPT_DIR"

    # Stop services
    log_info "Stopping services..."
    if ! docker-compose down; then
        log_error "Failed to stop services"
        return 1
    fi

    # Start services with new key
    log_info "Starting services with new API key..."
    if ! docker-compose up -d; then
        log_error "Failed to start services"
        return 1
    fi

    # Wait for services to stabilize
    log_info "Waiting for services to stabilize (10 seconds)..."
    sleep 10

    log_success "Services restarted successfully"
    return 0
}

# Check service health
check_service_health() {
    log_info "Checking service health..."

    cd "$SCRIPT_DIR"

    # Get list of running containers
    local running_containers
    running_containers=$(docker-compose ps --services --filter "status=running" 2>/dev/null || true)

    if [[ -z "$running_containers" ]]; then
        log_error "No services are running"
        return 1
    fi

    # Check each service
    local all_healthy=true
    while IFS= read -r service; do
        local status
        status=$(docker-compose ps "$service" 2>/dev/null | tail -n +2 | awk '{print $4}')

        if [[ "$status" == "running" ]] || [[ "$status" == "Up" ]]; then
            log_success "Service '$service' is healthy"
        else
            log_error "Service '$service' is not healthy (status: $status)"
            all_healthy=false
        fi
    done <<< "$running_containers"

    if [[ "$all_healthy" == true ]]; then
        log_success "All services are healthy"
        return 0
    else
        log_error "Some services are unhealthy"
        return 1
    fi
}

# Rollback to previous .env
rollback() {
    log_warning "Rolling back to previous configuration..."

    if [[ ! -f "$BACKUP_FILE" ]]; then
        log_error "Backup file not found: $BACKUP_FILE"
        log_error "Manual recovery required"
        return 1
    fi

    # Restore backup
    if cp "$BACKUP_FILE" "$ENV_FILE"; then
        log_success "Previous .env restored from backup"

        # Restart services with old key
        if restart_services; then
            log_success "Services restarted with previous configuration"
            log_info "Rollback completed successfully"
            return 0
        else
            log_error "Failed to restart services during rollback"
            return 1
        fi
    else
        log_error "Failed to restore backup"
        return 1
    fi
}

# Main execution
main() {
    echo ""
    log_info "OpenAI API Key Rotation Script"
    log_info "================================"
    echo ""

    # Parse command line arguments
    if [[ $# -lt 1 ]]; then
        show_help
    fi

    NEW_API_KEY=""
    DRY_RUN=false
    SKIP_VERIFY=false
    NO_RESTART=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-verify)
                SKIP_VERIFY=true
                shift
                ;;
            --no-restart)
                NO_RESTART=true
                shift
                ;;
            sk-*)
                NEW_API_KEY=$1
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                echo ""
                show_help
                ;;
        esac
    done

    if [[ -z "$NEW_API_KEY" ]]; then
        log_error "No API key provided"
        echo ""
        show_help
    fi

    # Step 1: Check prerequisites
    check_prerequisites
    echo ""

    # Step 2: Validate key format
    if ! validate_key_format "$NEW_API_KEY"; then
        log_error "Key validation failed"
        exit 1
    fi
    echo ""

    # Step 3: Verify API key
    if ! verify_api_key "$NEW_API_KEY"; then
        log_error "API key verification failed"
        exit 1
    fi
    echo ""

    # If dry run, stop here
    if [[ "$DRY_RUN" == true ]]; then
        log_success "Dry run completed successfully"
        log_info "Key is valid and ready for rotation"
        exit 0
    fi

    # Step 4: Backup current .env
    if ! backup_env_file; then
        log_error "Backup failed - aborting rotation"
        exit 1
    fi
    echo ""

    # Step 5: Update .env file
    if ! update_env_file "$NEW_API_KEY"; then
        log_error "Failed to update .env file"
        rollback
        exit 1
    fi
    echo ""

    # Step 6: Restart services (if not skipped)
    if [[ "$NO_RESTART" == false ]]; then
        if ! restart_services; then
            log_error "Failed to restart services"
            rollback
            exit 1
        fi
        echo ""

        # Step 7: Check service health
        if ! check_service_health; then
            log_error "Service health check failed"
            rollback
            exit 1
        fi
        echo ""
    else
        log_warning "Service restart skipped (--no-restart flag)"
        log_warning "You must manually restart services for changes to take effect"
        echo ""
    fi

    # Success summary
    log_success "========================================="
    log_success "OpenAI API Key Rotation Complete"
    log_success "========================================="
    echo ""
    log_info "Summary:"
    log_info "  - Backup: $BACKUP_FILE"
    log_info "  - New key length: ${#NEW_API_KEY} characters"
    if [[ "$NO_RESTART" == false ]]; then
        log_info "  - Services: Restarted and healthy"
    else
        log_info "  - Services: Not restarted (manual restart required)"
    fi
    echo ""
    log_info "Next steps:"
    log_info "  1. Test mem0 functionality to confirm new key works"
    log_info "  2. Revoke old API key at platform.openai.com"
    log_info "  3. Update any other systems using the old key"
    echo ""
    log_warning "IMPORTANT: Keep backup until you confirm everything works"
    log_info "Backup location: $BACKUP_FILE"
    echo ""
}

# Run main function
main "$@"
