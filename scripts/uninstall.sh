#!/usr/bin/env bash
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║   🗑️  NEXUS RELEASE AUTOMATION - UNINSTALL SCRIPT v2.3                   ║
# ║                                                                           ║
# ║   Safely removes all Nexus components with verification                  ║
# ║                                                                           ║
# ║   Usage: ./scripts/uninstall.sh [OPTIONS]                                ║
# ║                                                                           ║
# ║   Options:                                                                ║
# ║     --keep-env       Keep .env file (preserve credentials)               ║
# ║     --keep-data      Keep database volumes (preserve data)               ║
# ║     --keep-images    Keep Docker images (faster reinstall)               ║
# ║     --all            Remove everything including images and volumes      ║
# ║     --force, -f      Skip confirmation prompts                           ║
# ║     --dry-run        Show what would be removed without doing it         ║
# ║     --help, -h       Show this help message                              ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -u

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m'
BOLD='\033[1m'

# Options
KEEP_ENV=false
KEEP_DATA=false
KEEP_IMAGES=false
FORCE=false
DRY_RUN=false
REMOVE_ALL=false

# Counters
REMOVED_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

log() {
    local level=$1
    shift
    local message="$*"
    
    case $level in
        INFO)    echo -e "  ${BLUE}ℹ${NC}  $message" ;;
        SUCCESS) echo -e "  ${GREEN}✓${NC}  ${GREEN}$message${NC}" ;;
        WARNING) echo -e "  ${YELLOW}⚠${NC}  ${YELLOW}$message${NC}" ;;
        ERROR)   echo -e "  ${RED}✗${NC}  ${RED}$message${NC}" ;;
        STEP)
            echo ""
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${CYAN}${BOLD}  $message${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            ;;
        DRY)     echo -e "  ${GRAY}[DRY-RUN]${NC} Would remove: $message" ;;
    esac
}

print_banner() {
    echo ""
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                   ║${NC}"
    echo -e "${RED}║   ${WHITE}${BOLD}🗑️  NEXUS UNINSTALL${NC}${RED}                                          ║${NC}"
    echo -e "${RED}║                                                                   ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

confirm() {
    if [ "$FORCE" = true ]; then
        return 0
    fi
    
    local message="$1"
    echo -ne "  ${YELLOW}?${NC}  $message ${WHITE}[y/N]${NC} "
    read -r response
    
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

remove_item() {
    local item="$1"
    local type="$2"
    
    if [ "$DRY_RUN" = true ]; then
        log DRY "$type: $item"
        return 0
    fi
    
    if rm -rf "$item" 2>/dev/null; then
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
        return 0
    else
        FAILED_COUNT=$((FAILED_COUNT + 1))
        return 1
    fi
}

check_docker() {
    if ! command -v docker &>/dev/null; then
        return 1
    fi
    if ! docker info &>/dev/null; then
        return 1
    fi
    return 0
}

# ============================================================================
# DOCKER CLEANUP
# ============================================================================

stop_containers() {
    log STEP "Stopping Docker Containers"
    
    if ! check_docker; then
        log WARNING "Docker not available - skipping container cleanup"
        return 0
    fi
    
    local compose_file="$PROJECT_ROOT/infrastructure/docker/docker-compose.yml"
    if [ ! -f "$compose_file" ]; then
        compose_file="$PROJECT_ROOT/docker-compose.yml"
    fi
    
    if [ -f "$compose_file" ]; then
        log INFO "Stopping containers..."
        
        if [ "$DRY_RUN" = true ]; then
            local containers=$(docker compose -f "$compose_file" ps -q 2>/dev/null | wc -l | tr -d ' ')
            log DRY "Would stop $containers containers"
        else
            if docker compose -f "$compose_file" down --remove-orphans 2>/dev/null; then
                log SUCCESS "Containers stopped and removed"
            else
                log WARNING "Some containers may not have stopped cleanly"
            fi
        fi
    else
        log INFO "No docker-compose.yml found"
    fi
    
    # Also check for any orphan nexus containers
    local orphan_containers=$(docker ps -a --filter "name=nexus" --filter "name=docker-" -q 2>/dev/null)
    if [ -n "$orphan_containers" ]; then
        log INFO "Found orphan containers, removing..."
        if [ "$DRY_RUN" = true ]; then
            log DRY "Would remove orphan containers"
        else
            echo "$orphan_containers" | xargs -r docker rm -f 2>/dev/null || true
            log SUCCESS "Orphan containers removed"
        fi
    fi
}

remove_volumes() {
    log STEP "Removing Docker Volumes"
    
    if [ "$KEEP_DATA" = true ]; then
        log INFO "Keeping data volumes (--keep-data)"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return 0
    fi
    
    if ! check_docker; then
        log WARNING "Docker not available - skipping volume cleanup"
        return 0
    fi
    
    # Find nexus-related volumes
    local volumes=$(docker volume ls -q --filter "name=docker_" --filter "name=nexus" 2>/dev/null)
    
    if [ -n "$volumes" ]; then
        local count=$(echo "$volumes" | wc -l | tr -d ' ')
        log INFO "Found $count volume(s) to remove"
        
        for vol in $volumes; do
            if [ "$DRY_RUN" = true ]; then
                log DRY "Volume: $vol"
            else
                if docker volume rm "$vol" 2>/dev/null; then
                    log SUCCESS "Removed volume: $vol"
                    REMOVED_COUNT=$((REMOVED_COUNT + 1))
                else
                    log WARNING "Could not remove volume: $vol (may be in use)"
                    FAILED_COUNT=$((FAILED_COUNT + 1))
                fi
            fi
        done
    else
        log INFO "No volumes found"
    fi
}

remove_images() {
    log STEP "Removing Docker Images"
    
    if [ "$KEEP_IMAGES" = true ]; then
        log INFO "Keeping Docker images (--keep-images)"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return 0
    fi
    
    if ! check_docker; then
        log WARNING "Docker not available - skipping image cleanup"
        return 0
    fi
    
    # Find nexus-related images by name patterns
    local image_patterns=(
        "docker-orchestrator"
        "docker-jira-agent"
        "docker-git-ci-agent"
        "docker-reporting-agent"
        "docker-slack-agent"
        "docker-jira-hygiene-agent"
        "docker-rca-agent"
        "docker-analytics"
        "docker-webhooks"
        "docker-admin-dashboard"
        "nexus-*"
    )
    
    local removed=0
    local total=0
    
    for pattern in "${image_patterns[@]}"; do
        local images=$(docker images --filter "reference=$pattern" -q 2>/dev/null)
        
        if [ -n "$images" ]; then
            for image_id in $images; do
                total=$((total + 1))
                local image_name=$(docker images --format "{{.Repository}}:{{.Tag}}" --filter "id=$image_id" 2>/dev/null | head -1)
                
                if [ "$DRY_RUN" = true ]; then
                    log DRY "Image: $image_name ($image_id)"
                else
                    if docker rmi -f "$image_id" 2>/dev/null; then
                        log SUCCESS "Removed image: $image_name"
                        removed=$((removed + 1))
                        REMOVED_COUNT=$((REMOVED_COUNT + 1))
                    else
                        log WARNING "Could not remove image: $image_name"
                        FAILED_COUNT=$((FAILED_COUNT + 1))
                    fi
                fi
            done
        fi
    done
    
    if [ $total -eq 0 ]; then
        log INFO "No Nexus images found"
    elif [ "$DRY_RUN" = false ]; then
        log SUCCESS "Removed $removed/$total images"
    fi
    
    # Verify removal
    if [ "$DRY_RUN" = false ]; then
        echo ""
        log INFO "Verifying image removal..."
        local remaining=$(docker images --filter "reference=docker-*" -q 2>/dev/null | wc -l | tr -d ' ')
        if [ "$remaining" -gt 0 ]; then
            log WARNING "$remaining Nexus-related images still present:"
            docker images --filter "reference=docker-*" --format "  • {{.Repository}}:{{.Tag}} ({{.Size}})" 2>/dev/null
        else
            log SUCCESS "All Nexus images removed successfully"
        fi
    fi
}

remove_networks() {
    log STEP "Removing Docker Networks"
    
    if ! check_docker; then
        return 0
    fi
    
    local networks=$(docker network ls --filter "name=docker_" --filter "name=nexus" -q 2>/dev/null)
    
    if [ -n "$networks" ]; then
        for net in $networks; do
            local net_name=$(docker network inspect "$net" --format '{{.Name}}' 2>/dev/null)
            if [ "$DRY_RUN" = true ]; then
                log DRY "Network: $net_name"
            else
                if docker network rm "$net" 2>/dev/null; then
                    log SUCCESS "Removed network: $net_name"
                    REMOVED_COUNT=$((REMOVED_COUNT + 1))
                else
                    log WARNING "Could not remove network: $net_name"
                fi
            fi
        done
    else
        log INFO "No custom networks found"
    fi
}

# ============================================================================
# FILE CLEANUP
# ============================================================================

remove_venv() {
    log STEP "Removing Python Virtual Environment"
    
    if [ -d "$PROJECT_ROOT/venv" ]; then
        if [ "$DRY_RUN" = true ]; then
            local size=$(du -sh "$PROJECT_ROOT/venv" 2>/dev/null | cut -f1)
            log DRY "venv/ directory ($size)"
        else
            log INFO "Removing venv/..."
            if rm -rf "$PROJECT_ROOT/venv"; then
                log SUCCESS "Virtual environment removed"
                REMOVED_COUNT=$((REMOVED_COUNT + 1))
            else
                log ERROR "Failed to remove venv/"
                FAILED_COUNT=$((FAILED_COUNT + 1))
            fi
        fi
    else
        log INFO "No virtual environment found"
    fi
}

remove_env_file() {
    log STEP "Removing Environment File"
    
    if [ "$KEEP_ENV" = true ]; then
        log INFO "Keeping .env file (--keep-env)"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return 0
    fi
    
    if [ -f "$PROJECT_ROOT/.env" ]; then
        if [ "$DRY_RUN" = true ]; then
            log DRY ".env file"
        else
            log WARNING ".env contains your API credentials"
            if confirm "Are you sure you want to delete .env?"; then
                if rm -f "$PROJECT_ROOT/.env"; then
                    log SUCCESS ".env removed"
                    REMOVED_COUNT=$((REMOVED_COUNT + 1))
                else
                    log ERROR "Failed to remove .env"
                    FAILED_COUNT=$((FAILED_COUNT + 1))
                fi
            else
                log INFO "Keeping .env file"
                SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            fi
        fi
    else
        log INFO "No .env file found"
    fi
}

remove_generated_files() {
    log STEP "Removing Generated Files"
    
    local files_to_remove=(
        "$PROJECT_ROOT/setup.log"
        "$PROJECT_ROOT/.setup_checkpoint"
        "$PROJECT_ROOT/.setup.lock"
    )
    
    for file in "${files_to_remove[@]}"; do
        if [ -f "$file" ]; then
            local filename=$(basename "$file")
            if [ "$DRY_RUN" = true ]; then
                log DRY "$filename"
            else
                if rm -f "$file"; then
                    log SUCCESS "Removed $filename"
                    REMOVED_COUNT=$((REMOVED_COUNT + 1))
                fi
            fi
        fi
    done
    
    # Remove cache directories
    local cache_dirs=(
        "__pycache__"
        ".pytest_cache"
        ".mypy_cache"
        "*.egg-info"
        ".coverage"
        "htmlcov"
    )
    
    log INFO "Cleaning cache directories..."
    
    for pattern in "${cache_dirs[@]}"; do
        if [ "$DRY_RUN" = true ]; then
            local count=$(find "$PROJECT_ROOT" -type d -name "$pattern" 2>/dev/null | wc -l | tr -d ' ')
            if [ "$count" -gt 0 ]; then
                log DRY "$count $pattern directories"
            fi
        else
            find "$PROJECT_ROOT" -type d -name "$pattern" -exec rm -rf {} + 2>/dev/null || true
        fi
    done
    
    # Remove .pyc files
    if [ "$DRY_RUN" = true ]; then
        local pyc_count=$(find "$PROJECT_ROOT" -name "*.pyc" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$pyc_count" -gt 0 ]; then
            log DRY "$pyc_count .pyc files"
        fi
    else
        find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
        log SUCCESS "Cache files cleaned"
    fi
}

# ============================================================================
# SUMMARY
# ============================================================================

print_summary() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}  Uninstall Summary${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}DRY RUN${NC} - No changes were made"
        echo ""
        echo -e "  Run without ${CYAN}--dry-run${NC} to perform actual removal"
    else
        echo -e "  ${GREEN}Removed:${NC}  $REMOVED_COUNT items"
        echo -e "  ${YELLOW}Skipped:${NC}  $SKIPPED_COUNT items"
        if [ $FAILED_COUNT -gt 0 ]; then
            echo -e "  ${RED}Failed:${NC}   $FAILED_COUNT items"
        fi
        
        echo ""
        
        if [ $FAILED_COUNT -eq 0 ]; then
            echo -e "  ${GREEN}${BOLD}✓ Nexus has been successfully uninstalled${NC}"
        else
            echo -e "  ${YELLOW}⚠ Uninstall completed with some issues${NC}"
        fi
    fi
    
    echo ""
    echo -e "  ${CYAN}To reinstall:${NC}"
    echo -e "    ${WHITE}./scripts/setup.sh${NC}"
    echo ""
}

# ============================================================================
# HELP
# ============================================================================

show_help() {
    echo ""
    echo -e "${BOLD}Nexus Release Automation - Uninstall Script v2.3${NC}"
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./scripts/uninstall.sh [OPTIONS]"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --keep-env       Keep .env file (preserve credentials)"
    echo "  --keep-data      Keep database volumes (preserve data)"
    echo "  --keep-images    Keep Docker images (faster reinstall)"
    echo "  --all            Remove everything including all Docker resources"
    echo "  --force, -f      Skip confirmation prompts"
    echo "  --dry-run        Show what would be removed without doing it"
    echo "  --help, -h       Show this help message"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./scripts/uninstall.sh                    # Interactive uninstall"
    echo "  ./scripts/uninstall.sh --keep-env         # Keep credentials"
    echo "  ./scripts/uninstall.sh --dry-run          # Preview what would be removed"
    echo "  ./scripts/uninstall.sh --all --force      # Complete removal, no prompts"
    echo ""
    echo -e "${CYAN}What gets removed:${NC}"
    echo "  • Docker containers and networks"
    echo "  • Docker images (unless --keep-images)"
    echo "  • Docker volumes (unless --keep-data)"
    echo "  • Python virtual environment (venv/)"
    echo "  • Environment file (unless --keep-env)"
    echo "  • Generated files (logs, cache, etc.)"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --keep-env) KEEP_ENV=true; shift ;;
            --keep-data) KEEP_DATA=true; shift ;;
            --keep-images) KEEP_IMAGES=true; shift ;;
            --all) REMOVE_ALL=true; shift ;;
            --force|-f) FORCE=true; shift ;;
            --dry-run) DRY_RUN=true; shift ;;
            --help|-h) show_help; exit 0 ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    # If --all, override keep flags
    if [ "$REMOVE_ALL" = true ]; then
        KEEP_ENV=false
        KEEP_DATA=false
        KEEP_IMAGES=false
    fi
    
    # Print banner
    print_banner
    
    # Show what will be removed
    echo -e "  ${WHITE}This will remove:${NC}"
    echo -e "    • Docker containers and networks"
    [ "$KEEP_IMAGES" = false ] && echo -e "    • Docker images"
    [ "$KEEP_DATA" = false ] && echo -e "    • Docker volumes (database data)"
    echo -e "    • Python virtual environment"
    [ "$KEEP_ENV" = false ] && echo -e "    • Environment file (.env)"
    echo -e "    • Generated files and cache"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "  ${YELLOW}DRY RUN MODE${NC} - No actual changes will be made"
        echo ""
    else
        echo -e "  ${RED}${BOLD}⚠ This action cannot be undone!${NC}"
        echo ""
    fi
    
    # Confirm
    if [ "$DRY_RUN" = false ]; then
        if ! confirm "Are you sure you want to continue?"; then
            echo ""
            log INFO "Uninstall cancelled"
            exit 0
        fi
    fi
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Run cleanup steps
    stop_containers
    remove_volumes
    remove_images
    remove_networks
    remove_venv
    remove_env_file
    remove_generated_files
    
    # Print summary
    print_summary
}

# Run
main "$@"
