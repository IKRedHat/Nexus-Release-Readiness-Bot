#!/usr/bin/env bash
# ============================================================================
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║   ⚡ NEXUS RELEASE AUTOMATION - ONE-CLICK MASTER SCRIPT v3.0            ║
# ║                                                                           ║
# ║   The ultimate command center for Nexus operations                       ║
# ║                                                                           ║
# ║   Features:                                                               ║
# ║     • Interactive menu system                                            ║
# ║     • Full setup with resume capability                                  ║
# ║     • Service health monitoring                                          ║
# ║     • Log aggregation and analysis                                       ║
# ║     • Network diagnostics                                                ║
# ║     • Clean uninstall with backup                                        ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# ============================================================================

# Script identification
NEXUS_SCRIPT_NAME="nexus"
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
ENV_FILE="$NEXUS_PROJECT_ROOT/.env"
ENV_EXAMPLE="$NEXUS_PROJECT_ROOT/.env.example"

# Current operation mode
CURRENT_MODE="interactive"

# ============================================================================
# BANNER & MENUS
# ============================================================================

print_main_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
    
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗                    ║
    ║   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝                    ║
    ║   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗                    ║
    ║   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║                    ║
    ║   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║                    ║
    ║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝                    ║
    ║                                                                   ║
    ║           Release Automation Command Center v3.0                  ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝

EOF
    echo -e "${NC}"
    
    # Show system status
    show_quick_status
}

show_quick_status() {
    echo -e "  ${WHITE}System Status:${NC}"
    
    # Docker status
    if docker_running; then
        echo -e "    ${GREEN}●${NC} Docker: Running"
    else
        echo -e "    ${RED}●${NC} Docker: Not running"
    fi
    
    # Services status (quick check)
    local orchestrator_status
    orchestrator_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "http://localhost:8080/health" 2>/dev/null || echo "000")
    
    if [[ "$orchestrator_status" == "200" ]]; then
        echo -e "    ${GREEN}●${NC} Services: Online"
    else
        echo -e "    ${GRAY}●${NC} Services: Offline"
    fi
    
    # Environment
    if [[ -f "$ENV_FILE" ]]; then
        local mode
        mode=$(grep -E "^NEXUS_MOCK_MODE=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2)
        if [[ "$mode" == "true" ]]; then
            echo -e "    ${YELLOW}●${NC} Mode: Mock (Development)"
        else
            echo -e "    ${PURPLE}●${NC} Mode: Live (Production)"
        fi
    else
        echo -e "    ${GRAY}●${NC} Mode: Not configured"
    fi
    
    echo ""
}

print_main_menu() {
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}  Select an option:${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${GREEN}SETUP & INSTALL${NC}"
    echo -e "    ${WHITE}[1]${NC}  🚀 Quick Setup          - Full automated setup"
    echo -e "    ${WHITE}[2]${NC}  📦 Python Only          - Setup without Docker"
    echo -e "    ${WHITE}[3]${NC}  🐳 Docker Only          - Build and start containers"
    echo -e "    ${WHITE}[4]${NC}  🔄 Resume Setup         - Continue interrupted setup"
    echo ""
    echo -e "  ${CYAN}OPERATIONS${NC}"
    echo -e "    ${WHITE}[5]${NC}  ▶️  Start Services       - Start all Docker services"
    echo -e "    ${WHITE}[6]${NC}  ⏹️  Stop Services        - Stop all Docker services"
    echo -e "    ${WHITE}[7]${NC}  🔄 Restart Services     - Restart all services"
    echo -e "    ${WHITE}[8]${NC}  📋 View Logs            - Follow service logs"
    echo ""
    echo -e "  ${YELLOW}MONITORING${NC}"
    echo -e "    ${WHITE}[9]${NC}  ❤️  Health Check         - Check all service health"
    echo -e "    ${WHITE}[10]${NC} 📊 Service Status       - Detailed service status"
    echo -e "    ${WHITE}[11]${NC} 🌐 Network Diagnostics  - Test connectivity"
    echo -e "    ${WHITE}[12]${NC} 🧪 API Tests            - Run API endpoint tests"
    echo ""
    echo -e "  ${PURPLE}DEVELOPMENT${NC}"
    echo -e "    ${WHITE}[13]${NC} 🐚 Python Shell         - Interactive Python shell"
    echo -e "    ${WHITE}[14]${NC} 🔧 Dev Commands         - Common dev operations"
    echo -e "    ${WHITE}[15]${NC} 🎛️  Mode Toggle          - Switch Mock/Live mode"
    echo ""
    echo -e "  ${RED}CLEANUP${NC}"
    echo -e "    ${WHITE}[16]${NC} 🧹 Clean Containers     - Remove containers only"
    echo -e "    ${WHITE}[17]${NC} 🗑️  Uninstall            - Full uninstall wizard"
    echo ""
    echo -e "  ${GRAY}OTHER${NC}"
    echo -e "    ${WHITE}[18]${NC} 📖 Open Documentation   - View docs"
    echo -e "    ${WHITE}[19]${NC} 🌐 Open Dashboard       - Open Admin UI"
    echo -e "    ${WHITE}[0]${NC}  🚪 Exit"
    echo ""
    echo -ne "  Enter your choice: "
}

# ============================================================================
# SETUP OPERATIONS
# ============================================================================

do_quick_setup() {
    log STEP "Quick Setup - Full Automated Installation"
    
    # Check prerequisites
    echo ""
    log SUBSTEP "Checking prerequisites..."
    
    # Python
    if ! command_exists python3; then
        log ERROR "Python 3 is required. Please install Python 3.10+"
        wait_for_key
        return 1
    fi
    
    local python_version
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log SUCCESS "Python $python_version found"
    
    # Docker
    if ! check_docker_requirements; then
        log ERROR "Docker requirements not met"
        wait_for_key
        return 1
    fi
    
    # Network
    log SUBSTEP "Testing network connectivity..."
    if ! has_internet; then
        log WARNING "No internet connection detected"
        if ! confirm "Continue anyway?"; then
            return 1
        fi
    else
        log SUCCESS "Internet connectivity OK"
    fi
    
    # Run setup
    echo ""
    log STEP "Running Setup"
    save_state "setup_started" "$(date +%s)"
    
    # Virtual environment
    log SUBSTEP "Setting up Python virtual environment..."
    if [[ ! -d "$VENV_DIR" ]]; then
        if ! python3 -m venv "$VENV_DIR" >> "$NEXUS_LOG_FILE" 2>&1; then
            log ERROR "Failed to create virtual environment"
            wait_for_key
            return 1
        fi
    fi
    source "$VENV_DIR/bin/activate"
    log SUCCESS "Virtual environment ready"
    save_state "stage" "virtualenv"
    
    # Upgrade pip
    run_with_retry "Upgrading pip" pip install --upgrade pip
    
    # Install shared library
    if [[ -f "$NEXUS_PROJECT_ROOT/shared/setup.py" ]]; then
        run_with_retry "Installing nexus_lib" pip install -e "$NEXUS_PROJECT_ROOT/shared/"
        save_state "stage" "shared_lib"
    fi
    
    # Install service dependencies
    log SUBSTEP "Installing service dependencies..."
    local services=(
        "services/orchestrator"
        "services/agents/jira_agent"
        "services/agents/git_ci_agent"
        "services/agents/reporting_agent"
        "services/agents/slack_agent"
        "services/admin_dashboard/backend"
    )
    
    for service_path in "${services[@]}"; do
        local req_file="$NEXUS_PROJECT_ROOT/$service_path/requirements.txt"
        if [[ -f "$req_file" ]]; then
            local service_name
            service_name=$(basename "$service_path")
            run_with_retry "Installing $service_name dependencies" pip install -r "$req_file"
        fi
    done
    save_state "stage" "dependencies"
    
    # Environment file
    if [[ ! -f "$ENV_FILE" ]]; then
        log SUBSTEP "Creating environment file..."
        if [[ -f "$ENV_EXAMPLE" ]]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
        else
            create_default_env
        fi
        log SUCCESS ".env file created"
        log WARNING "Remember to update .env with your API credentials!"
    fi
    save_state "stage" "environment"
    
    # Docker build
    log SUBSTEP "Building Docker images (this may take a few minutes)..."
    if ! build_images >> "$NEXUS_LOG_FILE" 2>&1; then
        log ERROR "Docker build failed"
        log INFO "Check log: $NEXUS_LOG_FILE"
        wait_for_key
        return 1
    fi
    log SUCCESS "Docker images built"
    save_state "stage" "docker_build"
    
    # Start services
    log SUBSTEP "Starting services..."
    if ! start_containers >> "$NEXUS_LOG_FILE" 2>&1; then
        log ERROR "Failed to start services"
        wait_for_key
        return 1
    fi
    save_state "stage" "docker_start"
    
    # Wait for healthy
    log SUBSTEP "Waiting for services to be ready..."
    sleep 5
    
    # Clear state - setup complete
    clear_state
    
    # Show summary
    echo ""
    print_box "🎉 SETUP COMPLETE!"
    echo ""
    echo -e "  ${CYAN}Service URLs:${NC}"
    echo -e "    Admin Dashboard:  ${WHITE}http://localhost:8088${NC}"
    echo -e "    Orchestrator API: ${WHITE}http://localhost:8080${NC}"
    echo -e "    Grafana:          ${WHITE}http://localhost:3000${NC}"
    echo ""
    echo -e "  ${CYAN}Next Steps:${NC}"
    echo -e "    1. Update ${WHITE}.env${NC} with your API credentials"
    echo -e "    2. Visit the Admin Dashboard"
    echo -e "    3. Run health check to verify services"
    echo ""
    
    wait_for_key
}

do_python_only_setup() {
    log STEP "Python Only Setup"
    
    # Run setup with --skip-docker flag
    if [[ -x "$SCRIPT_DIR/setup.sh" ]]; then
        "$SCRIPT_DIR/setup.sh" --skip-docker
    else
        log ERROR "setup.sh not found or not executable"
    fi
    
    wait_for_key
}

do_docker_only_setup() {
    log STEP "Docker Only Setup"
    
    if ! check_docker_requirements; then
        wait_for_key
        return 1
    fi
    
    log SUBSTEP "Building Docker images..."
    if build_images; then
        log SUCCESS "Images built successfully"
    else
        log ERROR "Image build failed"
        wait_for_key
        return 1
    fi
    
    log SUBSTEP "Starting services..."
    if start_containers; then
        log SUCCESS "Services started"
        
        # Wait for healthy
        log SUBSTEP "Waiting for services..."
        sleep 10
        
        # Check health
        do_health_check
    fi
    
    wait_for_key
}

do_resume_setup() {
    log STEP "Resume Setup"
    
    local last_stage
    last_stage=$(get_state "stage")
    
    if [[ -z "$last_stage" ]]; then
        log INFO "No previous setup found. Starting fresh."
        do_quick_setup
        return
    fi
    
    log INFO "Resuming from stage: $last_stage"
    
    if [[ -x "$SCRIPT_DIR/setup.sh" ]]; then
        "$SCRIPT_DIR/setup.sh" --resume
    else
        log ERROR "setup.sh not found"
    fi
    
    wait_for_key
}

# ============================================================================
# SERVICE OPERATIONS
# ============================================================================

do_start_services() {
    log STEP "Starting Services"
    
    if ! docker_available; then
        log ERROR "Docker is not available"
        wait_for_key
        return 1
    fi
    
    log SUBSTEP "Starting all services..."
    
    if start_containers; then
        log SUCCESS "Services started"
        
        # Wait and check
        log SUBSTEP "Waiting for services to be ready..."
        sleep 5
        
        do_quick_health_check
    else
        log ERROR "Failed to start services"
    fi
    
    wait_for_key
}

do_stop_services() {
    log STEP "Stopping Services"
    
    log SUBSTEP "Stopping all services..."
    
    if stop_containers; then
        log SUCCESS "Services stopped"
    else
        log WARNING "Some services may not have stopped cleanly"
    fi
    
    wait_for_key
}

do_restart_services() {
    log STEP "Restarting Services"
    
    log SUBSTEP "Restarting all services..."
    
    if restart_containers; then
        log SUCCESS "Services restarted"
        
        sleep 5
        do_quick_health_check
    else
        log ERROR "Failed to restart services"
    fi
    
    wait_for_key
}

do_view_logs() {
    log STEP "View Logs"
    
    echo ""
    echo -e "  ${WHITE}Select service:${NC}"
    echo -e "    ${WHITE}[1]${NC}  All services"
    echo -e "    ${WHITE}[2]${NC}  Orchestrator"
    echo -e "    ${WHITE}[3]${NC}  Jira Agent"
    echo -e "    ${WHITE}[4]${NC}  Admin Dashboard"
    echo -e "    ${WHITE}[5]${NC}  Slack Agent"
    echo -e "    ${WHITE}[0]${NC}  Cancel"
    echo ""
    echo -ne "  Choice: "
    read -r choice
    
    case $choice in
        1) follow_logs ;;
        2) follow_logs orchestrator ;;
        3) follow_logs jira-agent ;;
        4) follow_logs admin-dashboard ;;
        5) follow_logs slack-agent ;;
        0) return ;;
        *) log WARNING "Invalid choice" ;;
    esac
}

# ============================================================================
# HEALTH & MONITORING
# ============================================================================

do_health_check() {
    log STEP "Service Health Check"
    
    # Register all services
    register_nexus_services
    register_observability_services
    
    # Run parallel health check
    check_services_parallel 5
    
    echo ""
}

do_quick_health_check() {
    # Quick inline health check
    register_nexus_services
    
    local healthy=0
    local total=0
    
    for service in "${NEXUS_SERVICES[@]}"; do
        IFS=':' read -r name url expected <<< "$service"
        ((total++))
        
        local code
        code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$url" 2>/dev/null || echo "000")
        
        if [[ "$code" == "200" ]]; then
            ((healthy++))
        fi
    done
    
    if [[ $healthy -eq $total ]]; then
        log SUCCESS "All $total services healthy"
    else
        log WARNING "$healthy/$total services healthy"
    fi
}

do_service_status() {
    log STEP "Service Status"
    
    if ! docker_available; then
        log ERROR "Docker is not available"
        wait_for_key
        return 1
    fi
    
    echo ""
    list_containers
    echo ""
    
    wait_for_key
}

do_network_diagnostics() {
    log STEP "Network Diagnostics"
    
    echo ""
    test_connectivity
    echo ""
    
    wait_for_key
}

do_api_tests() {
    log STEP "API Tests"
    
    if [[ -x "$SCRIPT_DIR/test-apis.sh" ]]; then
        "$SCRIPT_DIR/test-apis.sh"
    else
        log ERROR "test-apis.sh not found"
    fi
    
    wait_for_key
}

# ============================================================================
# DEVELOPMENT
# ============================================================================

do_python_shell() {
    log STEP "Python Shell"
    
    if [[ -f "$VENV_DIR/bin/activate" ]]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    echo ""
    echo -e "  ${CYAN}Nexus Development Shell${NC}"
    echo -e "  ${GRAY}Type 'exit()' to return to menu${NC}"
    echo ""
    
    python3 -i -c "
import sys
sys.path.insert(0, '$NEXUS_PROJECT_ROOT/shared')
print('Available: import nexus_lib')
print('Type exit() to return to menu')
print()
"
}

do_dev_commands() {
    log STEP "Development Commands"
    
    echo ""
    echo -e "  ${WHITE}Select command:${NC}"
    echo -e "    ${WHITE}[1]${NC}  Run tests"
    echo -e "    ${WHITE}[2]${NC}  Format code (black)"
    echo -e "    ${WHITE}[3]${NC}  Lint code (flake8)"
    echo -e "    ${WHITE}[4]${NC}  Type check (mypy)"
    echo -e "    ${WHITE}[5]${NC}  Rebuild single service"
    echo -e "    ${WHITE}[0]${NC}  Cancel"
    echo ""
    echo -ne "  Choice: "
    read -r choice
    
    if [[ -f "$VENV_DIR/bin/activate" ]]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    case $choice in
        1)
            echo ""
            pytest tests/ -v
            ;;
        2)
            echo ""
            black shared/ services/ --line-length 100
            ;;
        3)
            echo ""
            flake8 shared/ services/ --max-line-length=100 --ignore=E501,W503
            ;;
        4)
            echo ""
            mypy shared/ --ignore-missing-imports
            ;;
        5)
            echo -ne "  Service name: "
            read -r service_name
            build_images "$service_name"
            ;;
        0)
            return
            ;;
    esac
    
    wait_for_key
}

do_mode_toggle() {
    log STEP "Mode Toggle"
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log ERROR ".env file not found"
        wait_for_key
        return 1
    fi
    
    local current_mode
    current_mode=$(grep -E "^NEXUS_MOCK_MODE=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2)
    
    echo ""
    if [[ "$current_mode" == "true" ]]; then
        echo -e "  Current mode: ${YELLOW}Mock (Development)${NC}"
        echo ""
        
        if confirm "Switch to Live (Production) mode?"; then
            sed -i.bak 's/^NEXUS_MOCK_MODE=.*/NEXUS_MOCK_MODE=false/' "$ENV_FILE"
            log SUCCESS "Switched to Live mode"
            log WARNING "Remember to restart services!"
        fi
    else
        echo -e "  Current mode: ${PURPLE}Live (Production)${NC}"
        echo ""
        
        if confirm "Switch to Mock (Development) mode?"; then
            sed -i.bak 's/^NEXUS_MOCK_MODE=.*/NEXUS_MOCK_MODE=true/' "$ENV_FILE"
            log SUCCESS "Switched to Mock mode"
            log WARNING "Remember to restart services!"
        fi
    fi
    
    wait_for_key
}

# ============================================================================
# CLEANUP
# ============================================================================

do_clean_containers() {
    log STEP "Clean Containers"
    
    if confirm "Remove all Nexus containers?"; then
        stop_containers
        log SUCCESS "Containers removed"
    fi
    
    wait_for_key
}

do_uninstall() {
    log STEP "Uninstall Wizard"
    
    echo ""
    echo -e "  ${RED}${BOLD}⚠ WARNING${NC}"
    echo -e "  ${RED}This will remove Nexus components from your system.${NC}"
    echo ""
    
    if ! confirm "Are you sure you want to continue?"; then
        return
    fi
    
    echo ""
    echo -e "  ${WHITE}What would you like to remove?${NC}"
    echo ""
    
    local remove_containers=false
    local remove_images=false
    local remove_volumes=false
    local remove_venv=false
    local remove_env=false
    
    confirm "Remove Docker containers?" "y" && remove_containers=true
    confirm "Remove Docker images?" "n" && remove_images=true
    confirm "Remove Docker volumes (data)?" "n" && remove_volumes=true
    confirm "Remove Python virtual environment?" "n" && remove_venv=true
    confirm "Remove .env file?" "n" && remove_env=true
    
    echo ""
    log SUBSTEP "Creating backup..."
    local backup_dir
    backup_dir=$(create_backup "$ENV_FILE" 2>/dev/null || echo "")
    
    if $remove_containers; then
        log SUBSTEP "Removing containers..."
        stop_containers
    fi
    
    if $remove_volumes; then
        log SUBSTEP "Removing volumes..."
        remove_volumes --force
    fi
    
    if $remove_images; then
        log SUBSTEP "Removing images..."
        remove_images --force
    fi
    
    if $remove_venv && [[ -d "$VENV_DIR" ]]; then
        log SUBSTEP "Removing virtual environment..."
        rm -rf "$VENV_DIR"
        log SUCCESS "Virtual environment removed"
    fi
    
    if $remove_env && [[ -f "$ENV_FILE" ]]; then
        log SUBSTEP "Removing .env file..."
        rm -f "$ENV_FILE"
        log SUCCESS ".env file removed"
    fi
    
    # Cleanup state and logs
    rm -f "$NEXUS_STATE_FILE" "$NEXUS_LOCK_FILE" 2>/dev/null || true
    
    echo ""
    print_box "Uninstall Complete"
    
    if [[ -n "$backup_dir" ]]; then
        echo -e "  ${CYAN}Backup saved to:${NC} $backup_dir"
    fi
    
    echo ""
    echo -e "  ${CYAN}To reinstall:${NC} ./scripts/one-click.sh"
    echo ""
    
    wait_for_key
}

# ============================================================================
# OTHER
# ============================================================================

do_open_docs() {
    log STEP "Opening Documentation"
    
    local docs_url="file://$NEXUS_PROJECT_ROOT/docs/index.html"
    local readme="$NEXUS_PROJECT_ROOT/README.md"
    
    if command_exists open; then
        open "$readme"
    elif command_exists xdg-open; then
        xdg-open "$readme"
    else
        log INFO "View documentation at: $readme"
    fi
    
    wait_for_key
}

do_open_dashboard() {
    log STEP "Opening Dashboard"
    
    local url="http://localhost:8088"
    
    if command_exists open; then
        open "$url"
    elif command_exists xdg-open; then
        xdg-open "$url"
    else
        log INFO "Visit: $url"
    fi
    
    wait_for_key
}

# ============================================================================
# UTILITIES
# ============================================================================

wait_for_key() {
    echo ""
    echo -ne "  ${GRAY}Press any key to continue...${NC}"
    read -n 1 -s
    echo ""
}

create_default_env() {
    cat > "$ENV_FILE" << 'ENVEOF'
# NEXUS RELEASE AUTOMATION - ENVIRONMENT CONFIGURATION
# Generated by one-click.sh - Update with your credentials

NEXUS_ENV=development
NEXUS_MOCK_MODE=true
LOG_LEVEL=INFO

# LLM Configuration
LLM_PROVIDER=mock
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=

# Jira Configuration
JIRA_MOCK_MODE=true
JIRA_URL=https://your-company.atlassian.net
JIRA_API_TOKEN=

# GitHub Configuration
GITHUB_MOCK_MODE=true
GITHUB_TOKEN=

# Slack Configuration
SLACK_MOCK_MODE=true
SLACK_BOT_TOKEN=xoxb-
SLACK_SIGNING_SECRET=

# Redis
REDIS_URL=redis://redis:6379/0

# Security
NEXUS_JWT_SECRET=nexus-dev-jwt-secret-change-in-production
ENVEOF
}

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

show_cli_help() {
    print_help_header "nexus one-click.sh" "$NEXUS_SCRIPT_VERSION" "Nexus Command Center"
    
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./scripts/one-click.sh [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo "  setup           Run full automated setup"
    echo "  start           Start all services"
    echo "  stop            Stop all services"
    echo "  restart         Restart all services"
    echo "  status          Show service status"
    echo "  health          Run health check"
    echo "  logs [service]  View logs"
    echo "  test            Run API tests"
    echo "  uninstall       Run uninstall wizard"
    echo "  help            Show this help"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --verbose, -v   Show detailed output"
    echo "  --dry-run       Show what would be done"
    echo "  --non-interactive  Skip all prompts"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./scripts/one-click.sh                 # Interactive mode"
    echo "  ./scripts/one-click.sh setup           # Run setup directly"
    echo "  ./scripts/one-click.sh health          # Quick health check"
    echo "  ./scripts/one-click.sh logs orchestrator  # View specific logs"
    echo ""
}

handle_cli_command() {
    local command="${1:-}"
    shift 2>/dev/null || true
    
    case "$command" in
        setup)
            do_quick_setup
            ;;
        start)
            do_start_services
            ;;
        stop)
            do_stop_services
            ;;
        restart)
            do_restart_services
            ;;
        status)
            do_service_status
            ;;
        health)
            do_health_check
            ;;
        logs)
            if [[ -n "${1:-}" ]]; then
                follow_logs "$1"
            else
                follow_logs
            fi
            ;;
        test)
            do_api_tests
            ;;
        uninstall)
            do_uninstall
            ;;
        help|--help|-h)
            show_cli_help
            ;;
        *)
            return 1
            ;;
    esac
    
    return 0
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse global options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --verbose|-v)
                NEXUS_VERBOSE=true
                shift
                ;;
            --debug)
                NEXUS_DEBUG=true
                shift
                ;;
            --dry-run)
                NEXUS_DRY_RUN=true
                shift
                ;;
            --non-interactive)
                NEXUS_NON_INTERACTIVE=true
                shift
                ;;
            *)
                # Check if it's a command
                if handle_cli_command "$@"; then
                    exit 0
                fi
                shift
                ;;
        esac
    done
    
    # Interactive mode
    while true; do
        print_main_banner
        print_main_menu
        read -r choice
        
        case $choice in
            1)  do_quick_setup ;;
            2)  do_python_only_setup ;;
            3)  do_docker_only_setup ;;
            4)  do_resume_setup ;;
            5)  do_start_services ;;
            6)  do_stop_services ;;
            7)  do_restart_services ;;
            8)  do_view_logs ;;
            9)  do_health_check; wait_for_key ;;
            10) do_service_status ;;
            11) do_network_diagnostics ;;
            12) do_api_tests ;;
            13) do_python_shell ;;
            14) do_dev_commands ;;
            15) do_mode_toggle ;;
            16) do_clean_containers ;;
            17) do_uninstall ;;
            18) do_open_docs ;;
            19) do_open_dashboard ;;
            0)
                echo ""
                echo -e "  ${GREEN}Goodbye! 👋${NC}"
                echo ""
                exit 0
                ;;
            *)
                log WARNING "Invalid option: $choice"
                sleep 1
                ;;
        esac
    done
}

# Run main
main "$@"

