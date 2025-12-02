#!/usr/bin/env bash
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║   🚀 NEXUS RELEASE AUTOMATION - ONE-CLICK SETUP SCRIPT                   ║
# ║                                                                           ║
# ║   This script automates the complete setup process for the Nexus         ║
# ║   Release Automation System including:                                    ║
# ║     • Prerequisites verification and installation                         ║
# ║     • Python virtual environment setup                                    ║
# ║     • Dependency installation                                             ║
# ║     • Environment configuration                                           ║
# ║     • Docker services startup                                             ║
# ║     • Health verification                                                 ║
# ║                                                                           ║
# ║   Usage: ./scripts/setup.sh [OPTIONS]                                    ║
# ║                                                                           ║
# ║   Options:                                                                ║
# ║     --skip-docker     Skip Docker services startup                       ║
# ║     --skip-venv       Skip Python virtual environment setup              ║
# ║     --dev             Development mode (install dev dependencies)        ║
# ║     --clean           Clean existing setup before installing             ║
# ║     --help            Show this help message                              ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"
LOG_FILE="$PROJECT_ROOT/setup.log"

# Required versions
MIN_PYTHON_VERSION="3.10"
MIN_DOCKER_VERSION="20.10"
MIN_DOCKER_COMPOSE_VERSION="2.0"
MIN_NODE_VERSION="18.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Options
SKIP_DOCKER=false
SKIP_VENV=false
DEV_MODE=false
CLEAN_MODE=false

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_banner() {
    echo -e "${PURPLE}"
    cat << "EOF"
    
    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
    
    Release Automation System - v3.0
    LangGraph + MCP Architecture
    One-Click Setup Script
    
EOF
    echo -e "${NC}"
}

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Print to console with colors
    case $level in
        INFO)
            echo -e "${BLUE}ℹ${NC}  $message"
            ;;
        SUCCESS)
            echo -e "${GREEN}✓${NC}  $message"
            ;;
        WARNING)
            echo -e "${YELLOW}⚠${NC}  $message"
            ;;
        ERROR)
            echo -e "${RED}✗${NC}  $message"
            ;;
        STEP)
            echo -e "\n${CYAN}${BOLD}▶ $message${NC}"
            ;;
        SUBSTEP)
            echo -e "   ${WHITE}→${NC} $message"
            ;;
    esac
}

spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " ${CYAN}%c${NC}  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

run_with_spinner() {
    local message="$1"
    shift
    local cmd="$@"
    
    echo -ne "   ${WHITE}→${NC} $message... "
    
    # Run command in background and capture output
    ($cmd >> "$LOG_FILE" 2>&1) &
    local pid=$!
    spinner $pid
    wait $pid
    local status=$?
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

version_gte() {
    # Compare two version strings
    # Returns 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

get_os() {
    case "$(uname -s)" in
        Darwin*)  echo "macos" ;;
        Linux*)   echo "linux" ;;
        MINGW*|CYGWIN*|MSYS*) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

confirm() {
    local message="$1"
    local default="${2:-y}"
    
    if [ "$default" = "y" ]; then
        prompt="[Y/n]"
    else
        prompt="[y/N]"
    fi
    
    echo -ne "${YELLOW}?${NC}  $message $prompt "
    read -r response
    
    if [ -z "$response" ]; then
        response=$default
    fi
    
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

# ============================================================================
# PREREQUISITES CHECK
# ============================================================================

check_prerequisites() {
    log STEP "Checking Prerequisites"
    
    local all_ok=true
    local os=$(get_os)
    
    log SUBSTEP "Detected OS: $os"
    
    # Check Python
    log SUBSTEP "Checking Python..."
    if check_command python3; then
        local python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if version_gte "$python_version" "$MIN_PYTHON_VERSION"; then
            log SUCCESS "Python $python_version found (required: $MIN_PYTHON_VERSION+)"
        else
            log ERROR "Python $python_version is too old (required: $MIN_PYTHON_VERSION+)"
            all_ok=false
        fi
    else
        log ERROR "Python 3 not found"
        all_ok=false
        suggest_install_python "$os"
    fi
    
    # Check pip
    log SUBSTEP "Checking pip..."
    if check_command pip3 || python3 -m pip --version >/dev/null 2>&1; then
        log SUCCESS "pip found"
    else
        log WARNING "pip not found - will attempt to install"
    fi
    
    # Check Docker
    log SUBSTEP "Checking Docker..."
    if check_command docker; then
        local docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if version_gte "$docker_version" "$MIN_DOCKER_VERSION"; then
            log SUCCESS "Docker $docker_version found (required: $MIN_DOCKER_VERSION+)"
            
            # Check if Docker daemon is running
            if docker info >/dev/null 2>&1; then
                log SUCCESS "Docker daemon is running"
            else
                log WARNING "Docker daemon is not running"
                suggest_start_docker "$os"
            fi
        else
            log ERROR "Docker $docker_version is too old (required: $MIN_DOCKER_VERSION+)"
            all_ok=false
        fi
    else
        log WARNING "Docker not found - required for running services"
        suggest_install_docker "$os"
        if [ "$SKIP_DOCKER" = false ]; then
            all_ok=false
        fi
    fi
    
    # Check Docker Compose
    log SUBSTEP "Checking Docker Compose..."
    if docker compose version >/dev/null 2>&1; then
        local compose_version=$(docker compose version --short 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log SUCCESS "Docker Compose $compose_version found"
    elif check_command docker-compose; then
        local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log SUCCESS "Docker Compose (standalone) $compose_version found"
    else
        log WARNING "Docker Compose not found"
        if [ "$SKIP_DOCKER" = false ]; then
            all_ok=false
        fi
    fi
    
    # Check Git
    log SUBSTEP "Checking Git..."
    if check_command git; then
        log SUCCESS "Git found"
    else
        log WARNING "Git not found"
    fi
    
    # Check Node.js (for MCP sidecar servers)
    log SUBSTEP "Checking Node.js (for MCP servers)..."
    if check_command node; then
        local node_version=$(node --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if version_gte "$node_version" "$MIN_NODE_VERSION"; then
            log SUCCESS "Node.js $node_version found (required: $MIN_NODE_VERSION+)"
        else
            log WARNING "Node.js $node_version is old (recommended: $MIN_NODE_VERSION+)"
        fi
    else
        log INFO "Node.js not found (optional - needed for standard MCP servers like GitHub/Slack)"
        suggest_install_node "$os"
    fi
    
    # Check npm (for MCP server dependencies)
    log SUBSTEP "Checking npm..."
    if check_command npm; then
        log SUCCESS "npm found"
    else
        log INFO "npm not found (installed with Node.js)"
    fi
    
    # Optional: Check kubectl and Helm for Kubernetes deployment
    log SUBSTEP "Checking Kubernetes tools (optional)..."
    if check_command kubectl; then
        log SUCCESS "kubectl found"
    else
        log INFO "kubectl not found (optional - needed for K8s deployment)"
    fi
    
    if check_command helm; then
        log SUCCESS "Helm found"
    else
        log INFO "Helm not found (optional - needed for K8s deployment)"
    fi
    
    if [ "$all_ok" = false ]; then
        echo ""
        log ERROR "Some prerequisites are missing. Please install them and run this script again."
        echo ""
        echo -e "   ${YELLOW}Tip:${NC} Run with ${CYAN}--skip-docker${NC} to skip Docker-related checks"
        echo ""
        exit 1
    fi
    
    log SUCCESS "All prerequisites satisfied!"
}

suggest_install_python() {
    local os=$1
    echo ""
    echo -e "   ${YELLOW}To install Python:${NC}"
    case $os in
        macos)
            echo -e "   ${CYAN}brew install python@3.11${NC}"
            ;;
        linux)
            echo -e "   ${CYAN}sudo apt-get install python3.11 python3.11-venv${NC}  # Ubuntu/Debian"
            echo -e "   ${CYAN}sudo dnf install python3.11${NC}                       # Fedora/RHEL"
            ;;
    esac
    echo ""
}

suggest_install_docker() {
    local os=$1
    echo ""
    echo -e "   ${YELLOW}To install Docker:${NC}"
    case $os in
        macos)
            echo -e "   ${CYAN}brew install --cask docker${NC}"
            echo -e "   Or download from: https://docs.docker.com/desktop/mac/install/"
            ;;
        linux)
            echo -e "   ${CYAN}curl -fsSL https://get.docker.com | sh${NC}"
            echo -e "   Or visit: https://docs.docker.com/engine/install/"
            ;;
    esac
    echo ""
}

suggest_start_docker() {
    local os=$1
    echo ""
    echo -e "   ${YELLOW}To start Docker:${NC}"
    case $os in
        macos)
            echo -e "   ${CYAN}open -a Docker${NC}"
            ;;
        linux)
            echo -e "   ${CYAN}sudo systemctl start docker${NC}"
            ;;
    esac
    echo ""
}

suggest_install_node() {
    local os=$1
    echo ""
    echo -e "   ${YELLOW}To install Node.js (optional - for MCP sidecar servers):${NC}"
    case $os in
        macos)
            echo -e "   ${CYAN}brew install node@20${NC}"
            echo -e "   Or use nvm: ${CYAN}nvm install 20${NC}"
            ;;
        linux)
            echo -e "   ${CYAN}curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -${NC}"
            echo -e "   ${CYAN}sudo apt-get install -y nodejs${NC}"
            echo -e "   Or use nvm: ${CYAN}nvm install 20${NC}"
            ;;
    esac
    echo ""
}

# ============================================================================
# VIRTUAL ENVIRONMENT SETUP
# ============================================================================

setup_virtualenv() {
    if [ "$SKIP_VENV" = true ]; then
        log INFO "Skipping virtual environment setup (--skip-venv)"
        return
    fi
    
    log STEP "Setting Up Python Virtual Environment"
    
    # Clean existing venv if requested
    if [ "$CLEAN_MODE" = true ] && [ -d "$VENV_DIR" ]; then
        log SUBSTEP "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
        log SUCCESS "Removed existing venv"
    fi
    
    # Create virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        log SUBSTEP "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        log SUCCESS "Virtual environment created at $VENV_DIR"
    else
        log INFO "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    log SUBSTEP "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    log SUCCESS "Virtual environment activated"
    
    # Upgrade pip
    run_with_spinner "Upgrading pip" pip install --upgrade pip
    
    # Install wheel for faster installs
    run_with_spinner "Installing wheel" pip install wheel
}

# ============================================================================
# DEPENDENCY INSTALLATION
# ============================================================================

install_dependencies() {
    log STEP "Installing Python Dependencies"
    
    # Ensure we're in venv
    if [ "$SKIP_VENV" = false ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Install shared library
    log SUBSTEP "Installing shared library (nexus_lib)..."
    if [ -f "$PROJECT_ROOT/shared/setup.py" ]; then
        run_with_spinner "Installing nexus_lib" pip install -e "$PROJECT_ROOT/shared/"
    else
        log WARNING "shared/setup.py not found, skipping nexus_lib installation"
    fi
    
    # Install service dependencies
    local services=(
        "services/orchestrator"
        "services/agents/jira_agent"
        "services/agents/git_ci_agent"
        "services/agents/reporting_agent"
        "services/agents/slack_agent"
        "services/agents/jira_hygiene_agent"
        "services/agents/rca_agent"
        "services/analytics"
        "services/webhooks"
        "services/admin_dashboard/backend"
    )
    
    for service in "${services[@]}"; do
        local service_path="$PROJECT_ROOT/$service"
        local req_file="$service_path/requirements.txt"
        local service_name=$(basename "$service")
        
        if [ -f "$req_file" ]; then
            run_with_spinner "Installing $service_name dependencies" pip install -r "$req_file"
        else
            log WARNING "No requirements.txt found for $service_name"
        fi
    done
    
    # Install development dependencies if in dev mode
    if [ "$DEV_MODE" = true ]; then
        log SUBSTEP "Installing development dependencies..."
        run_with_spinner "Installing pytest" pip install pytest pytest-asyncio pytest-cov
        run_with_spinner "Installing linting tools" pip install black isort flake8 mypy
        log SUCCESS "Development dependencies installed"
    fi
    
    log SUCCESS "All dependencies installed!"
}

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

setup_environment() {
    log STEP "Configuring Environment"
    
    # Create .env file from example if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            log SUBSTEP "Creating .env from .env.example..."
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log SUCCESS "Created .env file"
        else
            log SUBSTEP "Creating default .env file..."
            create_default_env
            log SUCCESS "Created default .env file"
        fi
        
        echo ""
        log WARNING "Please review and update .env file with your credentials:"
        echo -e "   ${CYAN}$ENV_FILE${NC}"
        echo ""
    else
        log INFO ".env file already exists"
    fi
    
    # Source the environment file
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        log SUCCESS "Environment variables loaded"
    fi
}

create_default_env() {
    cat > "$ENV_FILE" << 'EOF'
# ============================================================================
# NEXUS RELEASE AUTOMATION - ENVIRONMENT CONFIGURATION
# ============================================================================
# Copy this file to .env and update with your credentials
# DO NOT commit .env to version control!
# ============================================================================

# General
NEXUS_ENV=development
LOG_LEVEL=INFO

# LLM Configuration
LLM_PROVIDER=mock                    # Options: google, openai, mock
LLM_MODEL=gemini-2.0-flash          # Model name
LLM_API_KEY=                         # Your API key (leave empty for mock mode)
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Memory/Vector Store
MEMORY_BACKEND=mock                  # Options: chromadb, pgvector, mock

# Multi-tenancy (optional)
MULTI_TENANT_ENABLED=false
DEFAULT_TENANT_PLAN=starter

# Jira Configuration
JIRA_MOCK_MODE=true                  # Set to false for real Jira
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=                      # Get from: https://id.atlassian.com/manage/api-tokens

# GitHub Configuration
GITHUB_MOCK_MODE=true
GITHUB_TOKEN=                        # Get from: https://github.com/settings/tokens

# Jenkins Configuration
JENKINS_MOCK_MODE=true
JENKINS_URL=https://jenkins.your-company.com
JENKINS_USERNAME=
JENKINS_API_TOKEN=

# Confluence Configuration
CONFLUENCE_MOCK_MODE=true
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=

# Slack Configuration
SLACK_MOCK_MODE=true
SLACK_BOT_TOKEN=xoxb-               # Bot User OAuth Token
SLACK_SIGNING_SECRET=                # Request signing secret
SLACK_APP_TOKEN=xapp-               # App-level token

# Hygiene Agent Configuration
HYGIENE_SCHEDULE_HOUR=9
HYGIENE_SCHEDULE_MINUTE=0
HYGIENE_SCHEDULE_DAYS=mon-fri
HYGIENE_TIMEZONE=UTC
HYGIENE_PROJECTS=                    # Comma-separated project keys (empty = all)

# Service URLs (for Docker networking)
ORCHESTRATOR_URL=http://orchestrator:8080
JIRA_AGENT_URL=http://jira-agent:8081
GITCI_AGENT_URL=http://git-ci-agent:8082
REPORTING_AGENT_URL=http://reporting-agent:8083
SLACK_AGENT_URL=http://slack-agent:8084
HYGIENE_AGENT_URL=http://jira-hygiene-agent:8005
RCA_AGENT_URL=http://rca-agent:8006
ANALYTICS_AGENT_URL=http://analytics:8086
WEBHOOKS_AGENT_URL=http://webhooks:8087
ADMIN_DASHBOARD_URL=http://admin-dashboard:8088

# RCA Agent Configuration
RCA_AUTO_ANALYZE=true
RCA_SLACK_NOTIFY=true
SLACK_RELEASE_CHANNEL=#release-notifications

# Webhooks Configuration
WEBHOOKS_HMAC_SECRET=your-webhook-secret-here
WEBHOOKS_RETRY_MAX=3
WEBHOOKS_RATE_LIMIT=100

# Database (for production)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=nexus
POSTGRES_USER=nexus
POSTGRES_PASSWORD=nexus_dev_password

# Redis (also used for dynamic configuration)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_URL=redis://redis:6379/0

# Dynamic Configuration
NEXUS_MOCK_MODE=true                 # Set to false for production mode

# JWT Secret (generate a strong random string for production)
NEXUS_JWT_SECRET=nexus-dev-jwt-secret-change-in-production

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
EOF
}

# ============================================================================
# DOCKER SERVICES
# ============================================================================

start_docker_services() {
    if [ "$SKIP_DOCKER" = true ]; then
        log INFO "Skipping Docker services startup (--skip-docker)"
        return
    fi
    
    log STEP "Starting Docker Services"
    
    cd "$PROJECT_ROOT"
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        log ERROR "docker-compose.yml not found in project root"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log ERROR "Docker daemon is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Stop existing containers if running
    log SUBSTEP "Stopping any existing containers..."
    docker compose down --remove-orphans >/dev/null 2>&1 || true
    
    # Build images
    log SUBSTEP "Building Docker images (this may take a few minutes)..."
    if docker compose build >> "$LOG_FILE" 2>&1; then
        log SUCCESS "Docker images built successfully"
    else
        log ERROR "Failed to build Docker images. Check $LOG_FILE for details."
        exit 1
    fi
    
    # Start services
    log SUBSTEP "Starting services..."
    if docker compose up -d >> "$LOG_FILE" 2>&1; then
        log SUCCESS "Docker services started"
    else
        log ERROR "Failed to start Docker services. Check $LOG_FILE for details."
        exit 1
    fi
    
    # Wait for services to be ready
    log SUBSTEP "Waiting for services to be ready..."
    sleep 5
}

# ============================================================================
# VERIFICATION
# ============================================================================

verify_setup() {
    log STEP "Verifying Setup"
    
    local all_ok=true
    
    # Check Python environment
    log SUBSTEP "Verifying Python environment..."
    if [ "$SKIP_VENV" = false ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    if python3 -c "import nexus_lib" 2>/dev/null; then
        log SUCCESS "nexus_lib is importable"
    else
        log WARNING "nexus_lib import failed (may need editable install)"
    fi
    
    # Check Docker services if not skipped
    if [ "$SKIP_DOCKER" = false ]; then
        log SUBSTEP "Checking service health..."
        
        local services=(
            "http://localhost:8080/health:Orchestrator"
            "http://localhost:8081/health:Jira Agent"
            "http://localhost:8082/health:Git/CI Agent"
            "http://localhost:8083/health:Reporting Agent"
            "http://localhost:8084/health:Slack Agent"
            "http://localhost:8005/health:Jira Hygiene Agent"
            "http://localhost:8006/health:RCA Agent"
            "http://localhost:8086/health:Analytics"
            "http://localhost:8087/health:Webhooks"
            "http://localhost:8088/health:Admin Dashboard"
        )
        
        for service in "${services[@]}"; do
            local url="${service%%:*}"
            local name="${service##*:}"
            
            # Retry a few times
            local max_retries=3
            local retry=0
            local success=false
            
            while [ $retry -lt $max_retries ]; do
                if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
                    success=true
                    break
                fi
                retry=$((retry + 1))
                sleep 2
            done
            
            if [ "$success" = true ]; then
                log SUCCESS "$name is healthy"
            else
                log WARNING "$name is not responding (may still be starting)"
                all_ok=false
            fi
        done
        
        # Check observability stack
        log SUBSTEP "Checking observability stack..."
        
        if curl -s --max-time 5 "http://localhost:9090/-/healthy" >/dev/null 2>&1; then
            log SUCCESS "Prometheus is healthy"
        else
            log WARNING "Prometheus is not responding"
        fi
        
        if curl -s --max-time 5 "http://localhost:3000/api/health" >/dev/null 2>&1; then
            log SUCCESS "Grafana is healthy"
        else
            log WARNING "Grafana is not responding"
        fi
    fi
    
    if [ "$all_ok" = true ]; then
        log SUCCESS "All verifications passed!"
    else
        log WARNING "Some services are not healthy yet. They may still be starting up."
        echo -e "   ${YELLOW}Tip:${NC} Run ${CYAN}docker compose logs -f${NC} to watch service logs"
    fi
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print_summary() {
    echo ""
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  🎉 NEXUS SETUP COMPLETE!${NC}"
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    if [ "$SKIP_VENV" = false ]; then
        echo -e "  ${CYAN}Activate virtual environment:${NC}"
        echo -e "    ${WHITE}source venv/bin/activate${NC}"
        echo ""
    fi
    
    if [ "$SKIP_DOCKER" = false ]; then
        echo -e "  ${CYAN}Service URLs:${NC}"
        echo -e "    ${WHITE}• Orchestrator API:    ${NC}http://localhost:8080"
        echo -e "    ${WHITE}• Orchestrator Docs:   ${NC}http://localhost:8080/docs"
        echo -e "    ${WHITE}• Hygiene Agent:       ${NC}http://localhost:8005"
        echo -e "    ${WHITE}• RCA Agent:           ${NC}http://localhost:8006"
        echo -e "    ${WHITE}• Analytics:           ${NC}http://localhost:8086"
        echo -e "    ${WHITE}• Webhooks:            ${NC}http://localhost:8087"
        echo -e "    ${WHITE}• Admin Dashboard:     ${NC}http://localhost:8088 ${YELLOW}(System Management)${NC}"
        echo -e "    ${WHITE}• Grafana Dashboard:   ${NC}http://localhost:3000 ${YELLOW}(admin/nexus_admin)${NC}"
        echo -e "    ${WHITE}• Prometheus:          ${NC}http://localhost:9090"
        echo -e "    ${WHITE}• Jaeger Tracing:      ${NC}http://localhost:16686"
        echo ""
        echo -e "  ${CYAN}Quick Commands:${NC}"
        echo -e "    ${WHITE}docker compose logs -f${NC}         # View logs"
        echo -e "    ${WHITE}docker compose ps${NC}              # Check status"
        echo -e "    ${WHITE}docker compose down${NC}            # Stop services"
        echo -e "    ${WHITE}docker compose restart${NC}         # Restart services"
        echo -e "    ${WHITE}./scripts/dev.sh help${NC}          # More dev commands"
        echo ""
    fi
    
    echo -e "  ${CYAN}Try a Query:${NC}"
    echo -e '    ${WHITE}curl -X POST http://localhost:8080/query \${NC}'
    echo -e '      ${WHITE}-H "Content-Type: application/json" \${NC}'
    echo -e '      ${WHITE}-d '"'"'{"query": "Is the v2.0 release ready?"}'"'"'${NC}'
    echo ""
    
    echo -e "  ${CYAN}Run a Hygiene Check:${NC}"
    echo -e '    ${WHITE}curl -X POST http://localhost:8005/run-check \${NC}'
    echo -e '      ${WHITE}-H "Content-Type: application/json" \${NC}'
    echo -e '      ${WHITE}-d '"'"'{"project_key": "PROJ", "notify": false}'"'"'${NC}'
    echo ""
    
    echo -e "  ${CYAN}Run Tests:${NC}"
    echo -e "    ${WHITE}pytest tests/ -v${NC}"
    echo ""
    
    echo -e "  ${CYAN}Documentation:${NC}"
    echo -e "    ${WHITE}• User Guide:    ${NC}docs/user_guide.md"
    echo -e "    ${WHITE}• Architecture:  ${NC}docs/architecture.md"
    echo -e "    ${WHITE}• API Reference: ${NC}docs/api-specs/overview.md"
    echo -e "    ${WHITE}• Deployment:    ${NC}docs/runbooks/deployment.md"
    echo ""
    
    if [ -f "$ENV_FILE" ]; then
        echo -e "  ${YELLOW}⚠ Remember to update .env with your API credentials!${NC}"
        echo ""
    fi
    
    echo -e "  ${PURPLE}Happy releasing! 🚀${NC}"
    echo ""
}

# ============================================================================
# HELP
# ============================================================================

show_help() {
    echo ""
    echo -e "${BOLD}Nexus Release Automation - Setup Script${NC}"
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./scripts/setup.sh [OPTIONS]"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --skip-docker     Skip Docker services startup"
    echo "  --skip-venv       Skip Python virtual environment setup"
    echo "  --dev             Development mode (install dev dependencies)"
    echo "  --clean           Clean existing setup before installing"
    echo "  --help            Show this help message"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./scripts/setup.sh                    # Full setup"
    echo "  ./scripts/setup.sh --dev              # Full setup with dev tools"
    echo "  ./scripts/setup.sh --skip-docker      # Python setup only"
    echo "  ./scripts/setup.sh --clean            # Fresh install"
    echo ""
    echo -e "${CYAN}Prerequisites:${NC}"
    echo "  • Python 3.10+"
    echo "  • Docker 20.10+ (optional with --skip-docker)"
    echo "  • Docker Compose 2.0+ (optional with --skip-docker)"
    echo "  • Node.js 18+ (optional - for standard MCP servers)"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-docker)
                SKIP_DOCKER=true
                shift
                ;;
            --skip-venv)
                SKIP_VENV=true
                shift
                ;;
            --dev)
                DEV_MODE=true
                shift
                ;;
            --clean)
                CLEAN_MODE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Clear log file
    > "$LOG_FILE"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Print banner
    print_banner
    
    # Run setup steps
    check_prerequisites
    setup_virtualenv
    install_dependencies
    setup_environment
    start_docker_services
    verify_setup
    
    # Print summary
    print_summary
}

# Run main function
main "$@"

