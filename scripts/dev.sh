#!/usr/bin/env bash
# ============================================================================
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║   🛠️  NEXUS RELEASE AUTOMATION - DEVELOPMENT HELPER v3.0                 ║
# ║                                                                           ║
# ║   Quick commands for common development tasks                            ║
# ║                                                                           ║
# ║   Features:                                                               ║
# ║     • Smart service management                                           ║
# ║     • Built-in retry logic                                               ║
# ║     • Colorized output                                                   ║
# ║     • API shortcuts                                                      ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# ============================================================================

# Script identification
NEXUS_SCRIPT_NAME="dev"
NEXUS_SCRIPT_VERSION="3.0.0"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source libraries
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/network.sh"
source "$SCRIPT_DIR/lib/docker.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

VENV_DIR="$NEXUS_PROJECT_ROOT/venv"

# Service ports
declare -A SERVICE_PORTS=(
    ["orchestrator"]=8080
    ["jira-agent"]=8081
    ["git-ci-agent"]=8082
    ["reporting-agent"]=8083
    ["slack-agent"]=8084
    ["jira-hygiene-agent"]=8085
    ["rca-agent"]=8006
    ["analytics"]=8086
    ["webhooks"]=8087
    ["admin-dashboard"]=8088
    ["prometheus"]=9090
    ["grafana"]=3000
    ["jaeger"]=16686
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

activate_venv() {
    if [[ -f "$VENV_DIR/bin/activate" ]]; then
        source "$VENV_DIR/bin/activate"
        return 0
    fi
    log WARNING "Virtual environment not found at $VENV_DIR"
    return 1
}

get_service_url() {
    local service="$1"
    local port="${SERVICE_PORTS[$service]:-}"
    
    if [[ -n "$port" ]]; then
        echo "http://localhost:$port"
    else
        log ERROR "Unknown service: $service"
        return 1
    fi
}

wait_for_service() {
    local service="$1"
    local max_wait="${2:-30}"
    local url
    url=$(get_service_url "$service")
    
    if [[ -z "$url" ]]; then
        return 1
    fi
    
    log INFO "Waiting for $service..."
    wait_for_url "$url/health" "$max_wait" 2
}

make_api_call() {
    local method="$1"
    local url="$2"
    local data="${3:-}"
    
    local response
    if [[ -n "$data" ]]; then
        response=$(curl -s -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$data" \
            --max-time 30 2>/dev/null)
    else
        response=$(curl -s -X "$method" "$url" \
            --max-time 30 2>/dev/null)
    fi
    
    # Pretty print JSON if available
    if command_exists jq; then
        echo "$response" | jq .
    elif command_exists python3; then
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        echo "$response"
    fi
}

# ============================================================================
# DOCKER COMMANDS
# ============================================================================

cmd_start() {
    log STEP "Starting Services"
    
    if ! docker_available; then
        log ERROR "Docker is not available"
        exit 1
    fi
    
    local services=("$@")
    
    if [[ ${#services[@]} -eq 0 ]]; then
        log SUBSTEP "Starting all services..."
        start_containers
    else
        log SUBSTEP "Starting: ${services[*]}"
        start_containers "${services[@]}"
    fi
    
    log SUCCESS "Services started!"
    echo ""
    log INFO "Use './scripts/dev.sh logs' to view logs"
}

cmd_stop() {
    log STEP "Stopping Services"
    
    local services=("$@")
    
    if [[ ${#services[@]} -eq 0 ]]; then
        log SUBSTEP "Stopping all services..."
        stop_containers
    else
        log SUBSTEP "Stopping: ${services[*]}"
        local cmd
        cmd=$(compose_cmd)
        $cmd stop "${services[@]}"
    fi
    
    log SUCCESS "Services stopped!"
}

cmd_restart() {
    log STEP "Restarting Services"
    
    local services=("$@")
    
    if [[ ${#services[@]} -eq 0 ]]; then
        log SUBSTEP "Restarting all services..."
        restart_containers
    else
        log SUBSTEP "Restarting: ${services[*]}"
        restart_containers "${services[@]}"
    fi
    
    log SUCCESS "Services restarted!"
}

cmd_logs() {
    local service="${1:-}"
    
    if [[ -n "$service" ]]; then
        log INFO "Following logs for: $service"
        follow_logs "$service"
    else
        log INFO "Following all logs (Ctrl+C to stop)"
        follow_logs
    fi
}

cmd_status() {
    log STEP "Service Status"
    echo ""
    list_containers
    echo ""
}

cmd_health() {
    "$SCRIPT_DIR/verify.sh" --services
}

cmd_clean() {
    log STEP "Cleaning Docker Resources"
    
    if confirm "Remove all containers and volumes?"; then
        log SUBSTEP "Stopping containers..."
        stop_containers
        
        log SUBSTEP "Removing volumes..."
        remove_volumes --force
        
        log SUCCESS "Cleanup complete!"
    else
        log INFO "Cleanup cancelled"
    fi
}

cmd_rebuild() {
    log STEP "Rebuild Services"
    
    local services=("$@")
    local no_cache=false
    
    # Check for --no-cache flag
    for arg in "${services[@]}"; do
        if [[ "$arg" == "--no-cache" ]]; then
            no_cache=true
            services=("${services[@]/$arg}")
        fi
    done
    
    log SUBSTEP "Stopping services..."
    stop_containers
    
    log SUBSTEP "Rebuilding images..."
    if $no_cache; then
        build_images --no-cache "${services[@]}"
    else
        build_images "${services[@]}"
    fi
    
    log SUBSTEP "Starting services..."
    start_containers
    
    log SUCCESS "Rebuild complete!"
}

cmd_pull() {
    log STEP "Pulling Latest Images"
    
    log SUBSTEP "Pulling base images..."
    pull_images
    
    log SUCCESS "Pull complete!"
}

# ============================================================================
# TESTING COMMANDS
# ============================================================================

cmd_test() {
    log STEP "Running Tests"
    
    activate_venv || exit 1
    
    local test_path="${1:-tests/}"
    
    log SUBSTEP "Running pytest..."
    pytest "$test_path" -v
}

cmd_test_unit() {
    log STEP "Running Unit Tests"
    
    activate_venv || exit 1
    
    log SUBSTEP "Running unit tests..."
    pytest tests/unit/ -v
}

cmd_test_e2e() {
    log STEP "Running E2E Tests"
    
    activate_venv || exit 1
    
    log SUBSTEP "Running e2e tests..."
    pytest tests/e2e/ -v
}

cmd_lint() {
    log STEP "Running Linters"
    
    activate_venv || exit 1
    
    log SUBSTEP "Running flake8..."
    flake8 shared/ services/ --max-line-length=120 --ignore=E501,W503 || true
    
    log SUBSTEP "Running mypy..."
    mypy shared/ --ignore-missing-imports || true
    
    log SUCCESS "Linting complete!"
}

cmd_format() {
    log STEP "Formatting Code"
    
    activate_venv || exit 1
    
    log SUBSTEP "Running black..."
    black shared/ services/ tests/ --line-length=100
    
    log SUBSTEP "Running isort..."
    isort shared/ services/ tests/
    
    log SUCCESS "Formatting complete!"
}

# ============================================================================
# API COMMANDS
# ============================================================================

cmd_query() {
    local query="$1"
    
    if [[ -z "$query" ]]; then
        log ERROR "Usage: ./scripts/dev.sh query \"your query here\""
        exit 1
    fi
    
    log INFO "Sending query to orchestrator..."
    echo ""
    
    make_api_call POST "http://localhost:8080/query" "{\"query\": \"$query\"}"
}

cmd_hygiene() {
    local project="${1:-PROJ}"
    
    log INFO "Running hygiene check for project: $project"
    echo ""
    
    make_api_call POST "http://localhost:8085/run-check" \
        "{\"project_key\": \"$project\", \"notify\": false}"
}

cmd_rca() {
    local job_name="$1"
    local build_number="$2"
    
    if [[ -z "$job_name" ]] || [[ -z "$build_number" ]]; then
        log ERROR "Usage: ./scripts/dev.sh rca <job_name> <build_number>"
        log INFO "Example: ./scripts/dev.sh rca nexus-main 142"
        exit 1
    fi
    
    log INFO "Analyzing build failure: $job_name #$build_number"
    echo ""
    
    make_api_call POST "http://localhost:8006/analyze" \
        "{\"job_name\": \"$job_name\", \"build_number\": $build_number, \"notify\": false}"
}

cmd_analytics() {
    local time_range="${1:-7d}"
    
    log INFO "Fetching analytics KPIs (range: $time_range)"
    echo ""
    
    make_api_call GET "http://localhost:8086/api/v1/kpis?time_range=$time_range"
}

cmd_mode() {
    local new_mode="${1:-}"
    
    if [[ -z "$new_mode" ]]; then
        log INFO "Current system mode:"
        echo ""
        make_api_call GET "http://localhost:8088/mode"
    else
        if [[ "$new_mode" != "mock" ]] && [[ "$new_mode" != "live" ]]; then
            log ERROR "Invalid mode. Use 'mock' or 'live'"
            exit 1
        fi
        
        log INFO "Setting system mode to: $new_mode"
        echo ""
        make_api_call POST "http://localhost:8088/mode" "{\"mode\": \"$new_mode\"}"
    fi
}

# ============================================================================
# OTHER COMMANDS
# ============================================================================

cmd_shell() {
    log STEP "Python Development Shell"
    
    activate_venv || exit 1
    
    echo ""
    echo -e "${CYAN}Nexus Development Shell${NC}"
    echo -e "${GRAY}nexus_lib is available for import${NC}"
    echo ""
    
    python3 -i -c "
import sys
sys.path.insert(0, '$NEXUS_PROJECT_ROOT/shared')
print('Available: import nexus_lib')
print('Type exit() to quit')
print()
"
}

cmd_admin() {
    local url="http://localhost:8088"
    
    log INFO "Opening Admin Dashboard: $url"
    
    if command_exists open; then
        open "$url"
    elif command_exists xdg-open; then
        xdg-open "$url"
    else
        log INFO "Visit: $url"
    fi
}

cmd_grafana() {
    local url="http://localhost:3000"
    
    log INFO "Opening Grafana: $url"
    log INFO "Default credentials: admin / nexus_admin"
    
    if command_exists open; then
        open "$url"
    elif command_exists xdg-open; then
        xdg-open "$url"
    else
        log INFO "Visit: $url (admin/nexus_admin)"
    fi
}

cmd_jaeger() {
    local url="http://localhost:16686"
    
    log INFO "Opening Jaeger: $url"
    
    if command_exists open; then
        open "$url"
    elif command_exists xdg-open; then
        xdg-open "$url"
    else
        log INFO "Visit: $url"
    fi
}

cmd_docs() {
    local url="http://localhost:8080/docs"
    
    log INFO "Opening API Documentation: $url"
    
    if command_exists open; then
        open "$url"
    elif command_exists xdg-open; then
        xdg-open "$url"
    else
        log INFO "Visit: $url"
    fi
}

cmd_sync_labels() {
    log STEP "Syncing GitHub Labels"
    
    activate_venv || exit 1
    
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        log ERROR "Set GITHUB_TOKEN environment variable first"
        exit 1
    fi
    
    python3 "$SCRIPT_DIR/sync_labels.py"
}

# ============================================================================
# HELP
# ============================================================================

show_help() {
    echo ""
    echo -e "${PURPLE}${BOLD}Nexus Development Helper v$NEXUS_SCRIPT_VERSION${NC}"
    echo ""
    echo -e "${CYAN}Usage:${NC} ./scripts/dev.sh <command> [options]"
    echo ""
    echo -e "${CYAN}Docker Commands:${NC}"
    echo "  start [services...]    Start services (all if none specified)"
    echo "  stop [services...]     Stop services"
    echo "  restart [services...]  Restart services"
    echo "  logs [service]         Follow logs (all if none specified)"
    echo "  status                 Show container status"
    echo "  health                 Run health checks"
    echo "  clean                  Remove containers and volumes"
    echo "  rebuild [--no-cache]   Rebuild and restart services"
    echo "  pull                   Pull latest base images"
    echo ""
    echo -e "${CYAN}Testing Commands:${NC}"
    echo "  test [path]            Run tests (default: tests/)"
    echo "  test-unit              Run unit tests"
    echo "  test-e2e               Run e2e tests"
    echo "  lint                   Run linters (flake8, mypy)"
    echo "  format                 Format code (black, isort)"
    echo ""
    echo -e "${CYAN}API Commands:${NC}"
    echo "  query \"text\"           Send query to orchestrator"
    echo "  hygiene [project]      Run hygiene check"
    echo "  rca <job> <build>      Analyze build failure"
    echo "  analytics [range]      Get analytics KPIs"
    echo "  mode [mock|live]       Get or set system mode"
    echo ""
    echo -e "${CYAN}Other Commands:${NC}"
    echo "  shell                  Open Python shell with nexus_lib"
    echo "  admin                  Open Admin Dashboard"
    echo "  grafana                Open Grafana"
    echo "  jaeger                 Open Jaeger"
    echo "  docs                   Open API documentation"
    echo "  sync-labels            Sync GitHub labels"
    echo "  help                   Show this help"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./scripts/dev.sh start                # Start all services"
    echo "  ./scripts/dev.sh start orchestrator   # Start single service"
    echo "  ./scripts/dev.sh logs slack-agent     # Follow service logs"
    echo "  ./scripts/dev.sh query \"What is my release status?\""
    echo "  ./scripts/dev.sh rebuild --no-cache   # Full rebuild"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    local command="${1:-help}"
    shift 2>/dev/null || true
    
    # Change to project root
    cd "$NEXUS_PROJECT_ROOT"
    
    case "$command" in
        # Docker commands
        start)      cmd_start "$@" ;;
        stop)       cmd_stop "$@" ;;
        restart)    cmd_restart "$@" ;;
        logs)       cmd_logs "$@" ;;
        status)     cmd_status ;;
        health)     cmd_health ;;
        clean)      cmd_clean ;;
        rebuild)    cmd_rebuild "$@" ;;
        pull)       cmd_pull ;;
        
        # Testing commands
        test)       cmd_test "$@" ;;
        test-unit)  cmd_test_unit ;;
        test-e2e)   cmd_test_e2e ;;
        lint)       cmd_lint ;;
        format)     cmd_format ;;
        
        # API commands
        query)      cmd_query "$@" ;;
        hygiene)    cmd_hygiene "$@" ;;
        rca)        cmd_rca "$@" ;;
        analytics)  cmd_analytics "$@" ;;
        mode)       cmd_mode "$@" ;;
        
        # Other commands
        shell)      cmd_shell ;;
        admin)      cmd_admin ;;
        grafana)    cmd_grafana ;;
        jaeger)     cmd_jaeger ;;
        docs)       cmd_docs ;;
        sync-labels) cmd_sync_labels ;;
        
        # Help
        help|--help|-h)
            show_help
            ;;
        
        *)
            log ERROR "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
