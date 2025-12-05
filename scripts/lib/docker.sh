#!/usr/bin/env bash
# ============================================================================
# NEXUS RELEASE AUTOMATION - DOCKER UTILITIES LIBRARY
# ============================================================================
# Version: 3.0.0
# Description: Docker and Docker Compose utilities
# ============================================================================
#
# REQUIRES: common.sh must be sourced first
#
# PROVIDES:
#   - Docker availability checks
#   - Compose file management
#   - Container management
#   - Image management
#   - Volume management
#   - Network management
#
# ============================================================================

# Ensure common.sh is loaded
if [[ -z "${__NEXUS_COMMON_LOADED:-}" ]]; then
    echo "ERROR: common.sh must be sourced before docker.sh" >&2
    exit 1
fi

# Prevent multiple sourcing
[[ -n "${__NEXUS_DOCKER_LOADED:-}" ]] && return
readonly __NEXUS_DOCKER_LOADED=1

# ============================================================================
# CONFIGURATION
# ============================================================================

# Docker compose files to search for
NEXUS_COMPOSE_FILES=(
    "infrastructure/docker/docker-compose.yml"
    "docker-compose.yml"
    "compose.yml"
)

# Cached compose file path
NEXUS_COMPOSE_FILE=""

# ============================================================================
# DOCKER AVAILABILITY
# ============================================================================

# Check if Docker is installed
# Usage: docker_installed && echo "Docker is installed"
docker_installed() {
    command_exists docker
}

# Check if Docker daemon is running
# Usage: docker_running && echo "Docker is running"
docker_running() {
    docker info &>/dev/null
}

# Check if Docker is fully available
# Usage: docker_available && echo "Docker is ready"
docker_available() {
    docker_installed && docker_running
}

# Get Docker version
# Usage: version=$(docker_version)
docker_version() {
    docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown"
}

# Check if Docker Compose is available
# Usage: compose_available && echo "Compose is ready"
compose_available() {
    docker compose version &>/dev/null
}

# Get Docker Compose version
# Usage: version=$(compose_version)
compose_version() {
    docker compose version --short 2>/dev/null || echo "unknown"
}

# ============================================================================
# DOCKER REQUIREMENTS CHECK
# ============================================================================

# Check all Docker requirements
# Usage: check_docker_requirements
check_docker_requirements() {
    local all_ok=true
    
    log SUBSTEP "Checking Docker requirements..."
    
    # Check Docker installation
    echo -ne "  ${WHITE}→${NC} Docker installed... "
    if docker_installed; then
        local version
        version=$(docker_version)
        echo -e "${GREEN}✓${NC} (v$version)"
    else
        echo -e "${RED}✗${NC}"
        all_ok=false
        
        local os
        os=$(get_os)
        echo -e "    ${YELLOW}Install Docker:${NC}"
        case $os in
            macos)
                echo -e "      ${CYAN}brew install --cask docker${NC}"
                echo -e "      or download from https://www.docker.com/products/docker-desktop"
                ;;
            linux)
                echo -e "      ${CYAN}curl -fsSL https://get.docker.com | sh${NC}"
                ;;
        esac
    fi
    
    # Check Docker daemon
    if docker_installed; then
        echo -ne "  ${WHITE}→${NC} Docker daemon running... "
        if docker_running; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            all_ok=false
            
            echo -e "    ${YELLOW}Start Docker:${NC}"
            case $(get_os) in
                macos)
                    echo -e "      ${CYAN}open -a Docker${NC}"
                    ;;
                linux)
                    echo -e "      ${CYAN}sudo systemctl start docker${NC}"
                    ;;
            esac
        fi
    fi
    
    # Check Docker Compose
    echo -ne "  ${WHITE}→${NC} Docker Compose... "
    if compose_available; then
        local compose_ver
        compose_ver=$(compose_version)
        echo -e "${GREEN}✓${NC} (v$compose_ver)"
    else
        echo -e "${RED}✗${NC}"
        all_ok=false
    fi
    
    # Check disk space
    echo -ne "  ${WHITE}→${NC} Disk space for Docker... "
    local available
    available=$(get_disk_space "/var/lib/docker" 2>/dev/null || get_disk_space ".")
    if [[ -n "$available" ]] && [[ "$available" -ge 5 ]]; then
        echo -e "${GREEN}✓${NC} (${available}GB available)"
    elif [[ -n "$available" ]]; then
        echo -e "${YELLOW}⚠${NC} (${available}GB - recommend 5GB+)"
    else
        echo -e "${GRAY}?${NC} (unable to check)"
    fi
    
    $all_ok
}

# ============================================================================
# COMPOSE FILE MANAGEMENT
# ============================================================================

# Find the compose file
# Usage: compose_file=$(find_compose_file)
find_compose_file() {
    if [[ -n "$NEXUS_COMPOSE_FILE" ]] && [[ -f "$NEXUS_COMPOSE_FILE" ]]; then
        echo "$NEXUS_COMPOSE_FILE"
        return 0
    fi
    
    local file
    for file in "${NEXUS_COMPOSE_FILES[@]}"; do
        local full_path="$NEXUS_PROJECT_ROOT/$file"
        if [[ -f "$full_path" ]]; then
            NEXUS_COMPOSE_FILE="$full_path"
            echo "$full_path"
            return 0
        fi
    done
    
    return 1
}

# Get compose command with file flag
# Usage: cmd=$(compose_cmd)
compose_cmd() {
    local compose_file
    compose_file=$(find_compose_file)
    
    if [[ -n "$compose_file" ]]; then
        echo "docker compose -f $compose_file"
    else
        echo "docker compose"
    fi
}

# ============================================================================
# CONTAINER MANAGEMENT
# ============================================================================

# List running Nexus containers
# Usage: list_containers
list_containers() {
    local cmd
    cmd=$(compose_cmd)
    $cmd ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
}

# Get container status
# Usage: status=$(container_status "container_name")
container_status() {
    local container="$1"
    docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || echo "not found"
}

# Check if container is running
# Usage: container_running "container_name" && echo "Running"
container_running() {
    local container="$1"
    [[ "$(container_status "$container")" == "running" ]]
}

# Get container health status
# Usage: health=$(container_health "container_name")
container_health() {
    local container="$1"
    docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no healthcheck"
}

# Start containers
# Usage: start_containers [service_names...]
start_containers() {
    local cmd
    cmd=$(compose_cmd)
    
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "$cmd up -d $*"
        return 0
    fi
    
    if [[ $# -eq 0 ]]; then
        $cmd up -d
    else
        $cmd up -d "$@"
    fi
}

# Stop containers
# Usage: stop_containers [service_names...]
stop_containers() {
    local cmd
    cmd=$(compose_cmd)
    
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "$cmd down $*"
        return 0
    fi
    
    if [[ $# -eq 0 ]]; then
        $cmd down --remove-orphans
    else
        $cmd stop "$@"
    fi
}

# Restart containers
# Usage: restart_containers [service_names...]
restart_containers() {
    local cmd
    cmd=$(compose_cmd)
    
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "$cmd restart $*"
        return 0
    fi
    
    if [[ $# -eq 0 ]]; then
        $cmd restart
    else
        $cmd restart "$@"
    fi
}

# Wait for containers to be healthy
# Usage: wait_for_healthy [timeout]
wait_for_healthy() {
    local timeout="${1:-120}"
    local cmd
    cmd=$(compose_cmd)
    local elapsed=0
    local interval=5
    
    while [[ $elapsed -lt $timeout ]]; do
        local all_healthy=true
        local containers
        containers=$($cmd ps -q 2>/dev/null)
        
        if [[ -z "$containers" ]]; then
            log WARNING "No containers running"
            return 1
        fi
        
        while IFS= read -r container; do
            local health
            health=$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
            
            if [[ "$health" == "unhealthy" ]]; then
                all_healthy=false
                break
            elif [[ "$health" == "starting" ]]; then
                all_healthy=false
            fi
        done <<< "$containers"
        
        if $all_healthy; then
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        progress_bar $elapsed $timeout "Waiting for containers"
    done
    
    echo ""
    return 1
}

# ============================================================================
# IMAGE MANAGEMENT
# ============================================================================

# Build Docker images
# Usage: build_images [--no-cache] [service_names...]
build_images() {
    local cmd
    cmd=$(compose_cmd)
    local args=()
    
    # Check for --no-cache flag
    if [[ "${1:-}" == "--no-cache" ]]; then
        args+=("--no-cache")
        shift
    fi
    
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "$cmd build ${args[*]} $*"
        return 0
    fi
    
    $cmd build "${args[@]}" "$@"
}

# List Nexus images
# Usage: list_images
list_images() {
    docker images --filter "reference=docker-*" --filter "reference=nexus-*" \
        --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"
}

# Remove Nexus images
# Usage: remove_images [--force]
remove_images() {
    local force="${1:-}"
    
    local images
    images=$(docker images --filter "reference=docker-*" --filter "reference=nexus-*" -q 2>/dev/null)
    
    if [[ -z "$images" ]]; then
        log INFO "No Nexus images found"
        return 0
    fi
    
    local count
    count=$(echo "$images" | wc -l | tr -d ' ')
    
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "Would remove $count image(s)"
        return 0
    fi
    
    log INFO "Removing $count image(s)..."
    
    local removed=0
    while IFS= read -r image; do
        if docker rmi ${force:+-f} "$image" &>/dev/null; then
            ((removed++))
        fi
    done <<< "$images"
    
    log SUCCESS "Removed $removed/$count images"
}

# Pull latest base images
# Usage: pull_images
pull_images() {
    local cmd
    cmd=$(compose_cmd)
    
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "$cmd pull"
        return 0
    fi
    
    $cmd pull
}

# ============================================================================
# VOLUME MANAGEMENT
# ============================================================================

# List Nexus volumes
# Usage: list_volumes
list_volumes() {
    docker volume ls --filter "name=docker_" --filter "name=nexus" \
        --format "table {{.Name}}\t{{.Driver}}" 2>/dev/null
}

# Remove Nexus volumes
# Usage: remove_volumes [--force]
remove_volumes() {
    local force="${1:-}"
    
    local volumes
    volumes=$(docker volume ls --filter "name=docker_" --filter "name=nexus" -q 2>/dev/null)
    
    if [[ -z "$volumes" ]]; then
        log INFO "No Nexus volumes found"
        return 0
    fi
    
    local count
    count=$(echo "$volumes" | wc -l | tr -d ' ')
    
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "Would remove $count volume(s)"
        return 0
    fi
    
    if [[ "$force" != "--force" ]] && [[ "$NEXUS_NON_INTERACTIVE" != "true" ]]; then
        if ! confirm "Remove $count volume(s)? (This deletes data!)"; then
            log INFO "Volume removal cancelled"
            return 0
        fi
    fi
    
    log INFO "Removing $count volume(s)..."
    
    local removed=0
    while IFS= read -r volume; do
        if docker volume rm "$volume" &>/dev/null; then
            ((removed++))
        fi
    done <<< "$volumes"
    
    log SUCCESS "Removed $removed/$count volumes"
}

# ============================================================================
# NETWORK MANAGEMENT
# ============================================================================

# List Nexus networks
# Usage: list_networks
list_networks() {
    docker network ls --filter "name=docker_" --filter "name=nexus" \
        --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" 2>/dev/null
}

# Remove Nexus networks
# Usage: remove_networks
remove_networks() {
    local networks
    networks=$(docker network ls --filter "name=docker_" --filter "name=nexus" -q 2>/dev/null)
    
    if [[ -z "$networks" ]]; then
        log INFO "No Nexus networks found"
        return 0
    fi
    
    local count
    count=$(echo "$networks" | wc -l | tr -d ' ')
    
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "Would remove $count network(s)"
        return 0
    fi
    
    log INFO "Removing $count network(s)..."
    
    local removed=0
    while IFS= read -r network; do
        if docker network rm "$network" &>/dev/null; then
            ((removed++))
        fi
    done <<< "$networks"
    
    log SUCCESS "Removed $removed/$count networks"
}

# ============================================================================
# CLEANUP UTILITIES
# ============================================================================

# Clean everything (containers, volumes, images, networks)
# Usage: docker_clean_all [--force]
docker_clean_all() {
    local force="${1:-}"
    
    log STEP "Cleaning Docker Resources"
    
    # Stop containers first
    log SUBSTEP "Stopping containers..."
    stop_containers
    
    # Remove volumes
    log SUBSTEP "Removing volumes..."
    remove_volumes "$force"
    
    # Remove images
    log SUBSTEP "Removing images..."
    remove_images "$force"
    
    # Remove networks
    log SUBSTEP "Removing networks..."
    remove_networks
    
    log SUCCESS "Docker cleanup complete"
}

# Prune unused Docker resources
# Usage: docker_prune
docker_prune() {
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "docker system prune -f"
        return 0
    fi
    
    docker system prune -f --volumes 2>/dev/null
}

# ============================================================================
# LOGS
# ============================================================================

# Get logs for services
# Usage: get_logs [service_name] [--follow] [--tail N]
get_logs() {
    local cmd
    cmd=$(compose_cmd)
    $cmd logs "$@"
}

# Follow logs for all services
# Usage: follow_logs [service_name]
follow_logs() {
    local cmd
    cmd=$(compose_cmd)
    $cmd logs -f "$@"
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f docker_installed docker_running docker_available docker_version
export -f compose_available compose_version
export -f check_docker_requirements
export -f find_compose_file compose_cmd
export -f list_containers container_status container_running container_health
export -f start_containers stop_containers restart_containers wait_for_healthy
export -f build_images list_images remove_images pull_images
export -f list_volumes remove_volumes
export -f list_networks remove_networks
export -f docker_clean_all docker_prune
export -f get_logs follow_logs

log DEBUG "Nexus docker library loaded"

