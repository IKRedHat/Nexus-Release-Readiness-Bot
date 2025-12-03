#!/usr/bin/env bash
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║   🚀 NEXUS RELEASE AUTOMATION - COMPREHENSIVE SETUP SCRIPT v2.3          ║
# ║                                                                           ║
# ║   Features:                                                               ║
# ║     • Checkpoint-based execution (resume from failure)                   ║
# ║     • Real-time progress with detailed messaging                         ║
# ║     • Automatic retry on network failures                                ║
# ║     • Comprehensive error handling and diagnostics                       ║
# ║     • Interactive and non-interactive modes                              ║
# ║                                                                           ║
# ║   Usage: ./scripts/setup.sh [OPTIONS]                                    ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# Exit on undefined variables, but handle errors manually
set -u

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"
LOG_FILE="$PROJECT_ROOT/setup.log"
CHECKPOINT_FILE="$PROJECT_ROOT/.setup_checkpoint"
LOCK_FILE="$PROJECT_ROOT/.setup.lock"

# Required versions
MIN_PYTHON_VERSION="3.10"
MIN_DOCKER_VERSION="20.10"

# Retry configuration
MAX_RETRIES=3
RETRY_DELAY=5
PIP_TIMEOUT=300  # 5 minutes per pip install

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Options (defaults)
SKIP_DOCKER=false
SKIP_VENV=false
DEV_MODE=false
CLEAN_MODE=false
RESUME_MODE=false
NON_INTERACTIVE=false
VERBOSE=false

# Setup stages
STAGES=(
    "prerequisites"
    "virtualenv"
    "shared_lib"
    "dependencies"
    "environment"
    "docker_build"
    "docker_start"
    "verification"
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_banner() {
    clear 2>/dev/null || true
    echo -e "${PURPLE}"
    cat << "EOF"
    
    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
    
EOF
    echo -e "    ${WHITE}Release Automation System ${CYAN}v2.3${NC}"
    echo -e "    ${GRAY}Comprehensive Setup Script${NC}"
    echo -e "${NC}"
}

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log_file() {
    echo "[$(timestamp)] $*" >> "$LOG_FILE"
}

# Enhanced logging with levels
log() {
    local level=$1
    shift
    local message="$*"
    
    log_file "[$level] $message"
    
    case $level in
        INFO)
            echo -e "  ${BLUE}ℹ${NC}  $message"
            ;;
        SUCCESS)
            echo -e "  ${GREEN}✓${NC}  ${GREEN}$message${NC}"
            ;;
        WARNING)
            echo -e "  ${YELLOW}⚠${NC}  ${YELLOW}$message${NC}"
            ;;
        ERROR)
            echo -e "  ${RED}✗${NC}  ${RED}$message${NC}"
            ;;
        DEBUG)
            if [ "$VERBOSE" = true ]; then
                echo -e "  ${GRAY}⋯${NC}  ${GRAY}$message${NC}"
            fi
            ;;
        STEP)
            echo ""
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${CYAN}${BOLD}  ▶ $message${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            ;;
        SUBSTEP)
            echo -e "  ${WHITE}→${NC} $message"
            ;;
        PROGRESS)
            echo -ne "\r  ${CYAN}⟳${NC}  $message"
            ;;
        PROGRESS_DONE)
            echo -e "\r  ${GREEN}✓${NC}  $message"
            ;;
    esac
}

# Progress bar for long operations
show_progress() {
    local current=$1
    local total=$2
    local message="${3:-Processing}"
    local width=40
    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    printf "\r  ${CYAN}⟳${NC}  %s [" "$message"
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] %3d%%" "$percent"
}

# Run command with timeout and retry
run_with_retry() {
    local description="$1"
    shift
    local cmd="$*"
    local attempt=1
    local status=0
    
    while [ $attempt -le $MAX_RETRIES ]; do
        log DEBUG "Attempt $attempt/$MAX_RETRIES: $cmd"
        
        # Show what we're doing
        if [ $attempt -eq 1 ]; then
            echo -ne "  ${WHITE}→${NC} $description... "
        else
            echo -ne "  ${YELLOW}↻${NC} Retry $attempt/$MAX_RETRIES: $description... "
        fi
        
        # Run command with timeout
        if timeout $PIP_TIMEOUT bash -c "$cmd" >> "$LOG_FILE" 2>&1; then
            echo -e "${GREEN}✓${NC}"
            return 0
        else
            status=$?
            echo -e "${RED}✗${NC}"
            
            if [ $attempt -lt $MAX_RETRIES ]; then
                log WARNING "Failed (exit: $status). Retrying in ${RETRY_DELAY}s..."
                sleep $RETRY_DELAY
            fi
        fi
        
        attempt=$((attempt + 1))
    done
    
    log ERROR "Failed after $MAX_RETRIES attempts: $description"
    return 1
}

# Run command with live output (for verbose mode or important steps)
run_live() {
    local description="$1"
    shift
    local cmd="$*"
    
    echo -e "  ${WHITE}→${NC} $description"
    
    if [ "$VERBOSE" = true ]; then
        # Show output in real-time
        if bash -c "$cmd" 2>&1 | tee -a "$LOG_FILE"; then
            log SUCCESS "Completed: $description"
            return 0
        else
            log ERROR "Failed: $description"
            return 1
        fi
    else
        # Show a progress indicator
        echo -ne "     ${GRAY}"
        if bash -c "$cmd" >> "$LOG_FILE" 2>&1 &
        then
            local pid=$!
            local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
            local i=0
            while kill -0 $pid 2>/dev/null; do
                i=$(( (i + 1) % 10 ))
                printf "\r     ${CYAN}%s${NC} ${GRAY}Running...${NC}" "${spin:$i:1}"
                sleep 0.1
            done
            wait $pid
            local status=$?
            printf "\r     "
            if [ $status -eq 0 ]; then
                echo -e "${GREEN}✓ Done${NC}                    "
                return 0
            else
                echo -e "${RED}✗ Failed${NC}                  "
                return 1
            fi
        fi
    fi
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

version_gte() {
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

# ============================================================================
# CHECKPOINT MANAGEMENT (Resume Support)
# ============================================================================

save_checkpoint() {
    local stage="$1"
    echo "$stage" > "$CHECKPOINT_FILE"
    log DEBUG "Checkpoint saved: $stage"
}

get_checkpoint() {
    if [ -f "$CHECKPOINT_FILE" ]; then
        cat "$CHECKPOINT_FILE"
    else
        echo ""
    fi
}

clear_checkpoint() {
    rm -f "$CHECKPOINT_FILE"
    log DEBUG "Checkpoint cleared"
}

should_skip_stage() {
    local stage="$1"
    local checkpoint=$(get_checkpoint)
    
    if [ -z "$checkpoint" ]; then
        return 1  # Don't skip, no checkpoint
    fi
    
    # Find positions
    local checkpoint_pos=-1
    local stage_pos=-1
    local i=0
    
    for s in "${STAGES[@]}"; do
        if [ "$s" = "$checkpoint" ]; then
            checkpoint_pos=$i
        fi
        if [ "$s" = "$stage" ]; then
            stage_pos=$i
        fi
        i=$((i + 1))
    done
    
    if [ $stage_pos -le $checkpoint_pos ]; then
        return 0  # Skip this stage
    fi
    
    return 1  # Don't skip
}

# ============================================================================
# LOCK FILE (Prevent concurrent runs)
# ============================================================================

acquire_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            log ERROR "Another setup process is running (PID: $pid)"
            log INFO "If this is incorrect, remove: $LOCK_FILE"
            exit 1
        fi
        rm -f "$LOCK_FILE"
    fi
    echo $$ > "$LOCK_FILE"
}

release_lock() {
    rm -f "$LOCK_FILE"
}

# ============================================================================
# CLEANUP ON EXIT
# ============================================================================

cleanup() {
    local exit_code=$?
    release_lock
    
    if [ $exit_code -ne 0 ]; then
        echo ""
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}${BOLD}  Setup Failed${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "  ${YELLOW}Troubleshooting:${NC}"
        echo -e "    • Check log file: ${CYAN}$LOG_FILE${NC}"
        echo -e "    • Run with verbose: ${CYAN}./scripts/setup.sh --verbose${NC}"
        echo -e "    • Resume from checkpoint: ${CYAN}./scripts/setup.sh --resume${NC}"
        echo ""
        local checkpoint=$(get_checkpoint)
        if [ -n "$checkpoint" ]; then
            echo -e "  ${GREEN}Progress saved!${NC} Last completed stage: ${CYAN}$checkpoint${NC}"
            echo -e "  Run ${CYAN}./scripts/setup.sh --resume${NC} to continue"
        fi
        echo ""
    fi
}

trap cleanup EXIT

# ============================================================================
# PREREQUISITES CHECK
# ============================================================================

check_prerequisites() {
    if [ "$RESUME_MODE" = true ] && should_skip_stage "prerequisites"; then
        log INFO "Skipping prerequisites (already completed)"
        return 0
    fi
    
    log STEP "Step 1/8: Checking Prerequisites"
    
    local all_ok=true
    local os=$(get_os)
    
    log SUBSTEP "Operating System: ${BOLD}$os${NC}"
    
    # Check Python
    log SUBSTEP "Checking Python..."
    if check_command python3; then
        local python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        local python_path=$(which python3)
        if version_gte "$python_version" "$MIN_PYTHON_VERSION"; then
            log SUCCESS "Python $python_version ✓ ($python_path)"
        else
            log ERROR "Python $python_version is too old (need $MIN_PYTHON_VERSION+)"
            all_ok=false
        fi
    else
        log ERROR "Python 3 not found"
        all_ok=false
        echo ""
        echo -e "  ${YELLOW}Install Python:${NC}"
        case $os in
            macos) echo -e "    ${CYAN}brew install python@3.11${NC}" ;;
            linux) echo -e "    ${CYAN}sudo apt install python3.11 python3.11-venv${NC}" ;;
        esac
        echo ""
    fi
    
    # Check pip
    log SUBSTEP "Checking pip..."
    if python3 -m pip --version >/dev/null 2>&1; then
        local pip_version=$(python3 -m pip --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log SUCCESS "pip $pip_version ✓"
    else
        log WARNING "pip not found - will attempt to install"
    fi
    
    # Check Docker (if not skipped)
    if [ "$SKIP_DOCKER" = false ]; then
        log SUBSTEP "Checking Docker..."
        if check_command docker; then
            local docker_version=$(docker --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
            if version_gte "$docker_version" "$MIN_DOCKER_VERSION"; then
                log SUCCESS "Docker $docker_version ✓"
                
                # Check daemon
                if docker info >/dev/null 2>&1; then
                    log SUCCESS "Docker daemon is running ✓"
                else
                    log ERROR "Docker daemon is not running"
                    echo ""
                    echo -e "  ${YELLOW}Start Docker:${NC}"
                    case $os in
                        macos) echo -e "    ${CYAN}open -a Docker${NC}" ;;
                        linux) echo -e "    ${CYAN}sudo systemctl start docker${NC}" ;;
                    esac
                    echo ""
                    all_ok=false
                fi
            else
                log ERROR "Docker $docker_version is too old (need $MIN_DOCKER_VERSION+)"
                all_ok=false
            fi
        else
            log ERROR "Docker not found"
            all_ok=false
        fi
        
        # Check Docker Compose
        log SUBSTEP "Checking Docker Compose..."
        if docker compose version >/dev/null 2>&1; then
            local compose_version=$(docker compose version --short 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
            log SUCCESS "Docker Compose $compose_version ✓"
        else
            log ERROR "Docker Compose not found"
            all_ok=false
        fi
    else
        log INFO "Skipping Docker checks (--skip-docker)"
    fi
    
    # Check Git
    log SUBSTEP "Checking Git..."
    if check_command git; then
        log SUCCESS "Git ✓"
    else
        log WARNING "Git not found (optional)"
    fi
    
    # Check disk space
    log SUBSTEP "Checking disk space..."
    local available_gb=$(df -BG "$PROJECT_ROOT" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
    if [ -n "$available_gb" ] && [ "$available_gb" -lt 5 ]; then
        log WARNING "Low disk space: ${available_gb}GB available (recommend 5GB+)"
    else
        log SUCCESS "Disk space: ${available_gb}GB available ✓"
    fi
    
    if [ "$all_ok" = false ]; then
        echo ""
        log ERROR "Prerequisites check failed. Please fix the issues above."
        echo ""
        echo -e "  ${YELLOW}Tip:${NC} Run with ${CYAN}--skip-docker${NC} to skip Docker checks"
        echo ""
        exit 1
    fi
    
    save_checkpoint "prerequisites"
    log SUCCESS "All prerequisites satisfied!"
}

# ============================================================================
# VIRTUAL ENVIRONMENT SETUP
# ============================================================================

setup_virtualenv() {
    if [ "$SKIP_VENV" = true ]; then
        log INFO "Skipping virtual environment (--skip-venv)"
        return 0
    fi
    
    if [ "$RESUME_MODE" = true ] && should_skip_stage "virtualenv"; then
        log INFO "Skipping virtualenv setup (already completed)"
        source "$VENV_DIR/bin/activate" 2>/dev/null || true
        return 0
    fi
    
    log STEP "Step 2/8: Setting Up Python Virtual Environment"
    
    # Clean if requested
    if [ "$CLEAN_MODE" = true ] && [ -d "$VENV_DIR" ]; then
        log SUBSTEP "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
        log SUCCESS "Removed old venv"
    fi
    
    # Create venv
    if [ ! -d "$VENV_DIR" ]; then
        log SUBSTEP "Creating virtual environment..."
        if python3 -m venv "$VENV_DIR"; then
            log SUCCESS "Virtual environment created at: $VENV_DIR"
        else
            log ERROR "Failed to create virtual environment"
            echo ""
            echo -e "  ${YELLOW}Try:${NC} ${CYAN}python3 -m pip install --user virtualenv${NC}"
            exit 1
        fi
    else
        log INFO "Virtual environment already exists"
    fi
    
    # Activate
    log SUBSTEP "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    log SUCCESS "Activated: $(which python)"
    
    # Upgrade pip
    log SUBSTEP "Upgrading pip..."
    run_with_retry "Upgrading pip" "pip install --upgrade pip"
    
    # Install wheel
    log SUBSTEP "Installing build tools..."
    run_with_retry "Installing wheel" "pip install wheel setuptools"
    
    save_checkpoint "virtualenv"
    log SUCCESS "Virtual environment ready!"
}

# ============================================================================
# DEPENDENCY INSTALLATION
# ============================================================================

install_shared_lib() {
    if [ "$RESUME_MODE" = true ] && should_skip_stage "shared_lib"; then
        log INFO "Skipping shared library (already completed)"
        return 0
    fi
    
    log STEP "Step 3/8: Installing Shared Library"
    
    # Activate venv if needed
    if [ "$SKIP_VENV" = false ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    if [ -f "$PROJECT_ROOT/shared/setup.py" ]; then
        log SUBSTEP "Installing nexus_lib (editable mode)..."
        if run_with_retry "Installing nexus_lib" "pip install -e '$PROJECT_ROOT/shared/'"; then
            # Verify installation
            if python3 -c "import nexus_lib; print(f'nexus_lib v{nexus_lib.__version__}')" 2>/dev/null; then
                log SUCCESS "nexus_lib installed and verified ✓"
            else
                log WARNING "nexus_lib installed but import verification failed"
            fi
        else
            log ERROR "Failed to install nexus_lib"
            exit 1
        fi
    else
        log WARNING "shared/setup.py not found - skipping nexus_lib"
    fi
    
    save_checkpoint "shared_lib"
}

install_dependencies() {
    if [ "$RESUME_MODE" = true ] && should_skip_stage "dependencies"; then
        log INFO "Skipping dependencies (already completed)"
        return 0
    fi
    
    log STEP "Step 4/8: Installing Service Dependencies"
    
    # Activate venv if needed
    if [ "$SKIP_VENV" = false ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Define services with their paths
    local -A services=(
        ["orchestrator"]="services/orchestrator"
        ["jira_agent"]="services/agents/jira_agent"
        ["git_ci_agent"]="services/agents/git_ci_agent"
        ["reporting_agent"]="services/agents/reporting_agent"
        ["slack_agent"]="services/agents/slack_agent"
        ["jira_hygiene_agent"]="services/agents/jira_hygiene_agent"
        ["rca_agent"]="services/agents/rca_agent"
        ["analytics"]="services/analytics"
        ["webhooks"]="services/webhooks"
        ["admin_dashboard"]="services/admin_dashboard/backend"
    )
    
    local total=${#services[@]}
    local current=0
    local failed=()
    
    echo ""
    log INFO "Installing dependencies for $total services..."
    echo ""
    
    for service in "${!services[@]}"; do
        current=$((current + 1))
        local path="${services[$service]}"
        local req_file="$PROJECT_ROOT/$path/requirements.txt"
        
        if [ -f "$req_file" ]; then
            # Show progress
            local progress_msg="[$current/$total] $service"
            
            if run_with_retry "$progress_msg" "pip install -r '$req_file'"; then
                log_file "SUCCESS: $service dependencies installed"
            else
                failed+=("$service")
                log WARNING "Failed to install $service dependencies (will retry later)"
            fi
        else
            log DEBUG "No requirements.txt for $service"
        fi
    done
    
    # Retry failed installations
    if [ ${#failed[@]} -gt 0 ]; then
        echo ""
        log WARNING "Retrying ${#failed[@]} failed installations..."
        
        for service in "${failed[@]}"; do
            local path="${services[$service]}"
            local req_file="$PROJECT_ROOT/$path/requirements.txt"
            
            if ! run_with_retry "Retry: $service" "pip install -r '$req_file'"; then
                log ERROR "Failed to install $service after retries"
                echo ""
                echo -e "  ${YELLOW}Try manually:${NC}"
                echo -e "    ${CYAN}pip install -r $path/requirements.txt${NC}"
                echo ""
            fi
        done
    fi
    
    # Install dev dependencies if requested
    if [ "$DEV_MODE" = true ]; then
        echo ""
        log SUBSTEP "Installing development tools..."
        run_with_retry "pytest & testing tools" "pip install pytest pytest-asyncio pytest-cov httpx"
        run_with_retry "linting tools" "pip install black isort flake8 mypy"
        log SUCCESS "Development tools installed"
    fi
    
    save_checkpoint "dependencies"
    log SUCCESS "Dependencies installation complete!"
}

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

setup_environment() {
    if [ "$RESUME_MODE" = true ] && should_skip_stage "environment"; then
        log INFO "Skipping environment config (already completed)"
        return 0
    fi
    
    log STEP "Step 5/8: Configuring Environment"
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            log SUBSTEP "Creating .env from .env.example..."
            cp "$ENV_EXAMPLE" "$ENV_FILE"
        else
            log SUBSTEP "Creating default .env file..."
            create_default_env
        fi
        log SUCCESS "Created .env file"
        
        echo ""
        echo -e "  ${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "  ${YELLOW}⚠${NC}  ${BOLD}ACTION REQUIRED${NC}"
        echo -e "  ${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "  Please update ${CYAN}.env${NC} with your API credentials:"
        echo -e "    • Jira API token"
        echo -e "    • GitHub token"
        echo -e "    • Slack tokens"
        echo -e "    • LLM API key (if using Gemini/OpenAI)"
        echo -e "  ${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
    else
        log INFO ".env file already exists"
    fi
    
    # Source environment
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE" 2>/dev/null || true
        set +a
        log SUCCESS "Environment variables loaded"
    fi
    
    save_checkpoint "environment"
}

create_default_env() {
    cat > "$ENV_FILE" << 'ENVEOF'
# ============================================================================
# NEXUS RELEASE AUTOMATION - ENVIRONMENT CONFIGURATION
# ============================================================================
# Generated by setup.sh - Update with your credentials
# DO NOT commit this file to version control!
# ============================================================================

# General Settings
NEXUS_ENV=development
NEXUS_MOCK_MODE=true                 # Set to false for production
LOG_LEVEL=INFO

# LLM Configuration
LLM_PROVIDER=mock                    # Options: google, openai, mock
LLM_MODEL=gemini-2.0-flash
LLM_API_KEY=                         # Your API key
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Jira Configuration
JIRA_MOCK_MODE=true
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=

# GitHub Configuration
GITHUB_MOCK_MODE=true
GITHUB_TOKEN=

# Jenkins Configuration
JENKINS_MOCK_MODE=true
JENKINS_URL=https://jenkins.your-company.com
JENKINS_USERNAME=
JENKINS_API_TOKEN=

# Slack Configuration
SLACK_MOCK_MODE=true
SLACK_BOT_TOKEN=xoxb-
SLACK_SIGNING_SECRET=
SLACK_APP_TOKEN=xapp-

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=nexus
POSTGRES_USER=nexus
POSTGRES_PASSWORD=nexus_dev_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# Service URLs (Docker)
ORCHESTRATOR_URL=http://orchestrator:8080
JIRA_AGENT_URL=http://jira-agent:8081
GIT_AGENT_URL=http://git-ci-agent:8082
REPORTING_AGENT_URL=http://reporting-agent:8083
SLACK_AGENT_URL=http://slack-agent:8084
HYGIENE_AGENT_URL=http://jira-hygiene-agent:8005
RCA_AGENT_URL=http://rca-agent:8006
ANALYTICS_URL=http://analytics:8086
WEBHOOKS_URL=http://webhooks:8087
ADMIN_DASHBOARD_URL=http://admin-dashboard:8088

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus

# Security
NEXUS_JWT_SECRET=nexus-dev-jwt-secret-change-in-production
ENVEOF
}

# ============================================================================
# DOCKER SERVICES
# ============================================================================

build_docker_images() {
    if [ "$SKIP_DOCKER" = true ]; then
        log INFO "Skipping Docker build (--skip-docker)"
        return 0
    fi
    
    if [ "$RESUME_MODE" = true ] && should_skip_stage "docker_build"; then
        log INFO "Skipping Docker build (already completed)"
        return 0
    fi
    
    log STEP "Step 6/8: Building Docker Images"
    
    cd "$PROJECT_ROOT"
    
    # Check docker-compose
    local compose_file="infrastructure/docker/docker-compose.yml"
    if [ ! -f "$compose_file" ]; then
        compose_file="docker-compose.yml"
    fi
    
    if [ ! -f "$compose_file" ]; then
        log ERROR "docker-compose.yml not found"
        exit 1
    fi
    
    log INFO "This may take 5-15 minutes on first run..."
    echo ""
    
    # Build with progress
    log SUBSTEP "Building all service images..."
    
    if [ "$VERBOSE" = true ]; then
        docker compose -f "$compose_file" build 2>&1 | tee -a "$LOG_FILE"
    else
        echo -e "  ${GRAY}Building images (check $LOG_FILE for details)...${NC}"
        if docker compose -f "$compose_file" build >> "$LOG_FILE" 2>&1; then
            log SUCCESS "All Docker images built successfully!"
        else
            log ERROR "Docker build failed. Check $LOG_FILE for details."
            echo ""
            echo -e "  ${YELLOW}Common fixes:${NC}"
            echo -e "    • Ensure Docker daemon is running"
            echo -e "    • Check available disk space"
            echo -e "    • Run ${CYAN}docker system prune${NC} to free space"
            echo ""
            exit 1
        fi
    fi
    
    # List built images
    log SUBSTEP "Built images:"
    docker images --filter "reference=docker-*" --format "  • {{.Repository}}:{{.Tag}} ({{.Size}})" | head -15
    
    save_checkpoint "docker_build"
}

start_docker_services() {
    if [ "$SKIP_DOCKER" = true ]; then
        log INFO "Skipping Docker startup (--skip-docker)"
        return 0
    fi
    
    if [ "$RESUME_MODE" = true ] && should_skip_stage "docker_start"; then
        log INFO "Skipping Docker startup (already completed)"
        return 0
    fi
    
    log STEP "Step 7/8: Starting Docker Services"
    
    cd "$PROJECT_ROOT"
    
    local compose_file="infrastructure/docker/docker-compose.yml"
    if [ ! -f "$compose_file" ]; then
        compose_file="docker-compose.yml"
    fi
    
    # Stop existing
    log SUBSTEP "Stopping any existing containers..."
    docker compose -f "$compose_file" down --remove-orphans >/dev/null 2>&1 || true
    
    # Start services
    log SUBSTEP "Starting all services..."
    if docker compose -f "$compose_file" up -d >> "$LOG_FILE" 2>&1; then
        log SUCCESS "Services started!"
    else
        log ERROR "Failed to start services"
        exit 1
    fi
    
    # Wait for services
    log SUBSTEP "Waiting for services to be ready..."
    local wait_time=30
    local elapsed=0
    
    while [ $elapsed -lt $wait_time ]; do
        local healthy=$(docker compose -f "$compose_file" ps --format json 2>/dev/null | grep -c '"healthy"' || echo "0")
        show_progress $elapsed $wait_time "Waiting for services ($healthy healthy)"
        sleep 2
        elapsed=$((elapsed + 2))
    done
    echo ""
    
    save_checkpoint "docker_start"
    log SUCCESS "Docker services are running!"
}

# ============================================================================
# VERIFICATION
# ============================================================================

verify_setup() {
    if [ "$RESUME_MODE" = true ] && should_skip_stage "verification"; then
        log INFO "Skipping verification (already completed)"
        return 0
    fi
    
    log STEP "Step 8/8: Verifying Setup"
    
    local all_ok=true
    
    # Verify Python
    if [ "$SKIP_VENV" = false ]; then
        source "$VENV_DIR/bin/activate" 2>/dev/null || true
    fi
    
    log SUBSTEP "Verifying Python packages..."
    if python3 -c "import nexus_lib" 2>/dev/null; then
        log SUCCESS "nexus_lib ✓"
    else
        log WARNING "nexus_lib import failed"
    fi
    
    # Verify Docker services
    if [ "$SKIP_DOCKER" = false ]; then
        echo ""
        log SUBSTEP "Checking service health..."
        echo ""
        
        local services=(
            "8080:Orchestrator"
            "8081:Jira Agent"
            "8082:Git/CI Agent"
            "8083:Reporting Agent"
            "8084:Slack Agent"
            "8085:Jira Hygiene Agent"
            "8006:RCA Agent"
            "8086:Analytics"
            "8087:Webhooks"
            "8088:Admin Dashboard"
        )
        
        echo -e "  ${WHITE}┌──────────────────────────────────────────┐${NC}"
        echo -e "  ${WHITE}│${NC}  ${BOLD}Nexus Service Health Check${NC}               ${WHITE}│${NC}"
        echo -e "  ${WHITE}├──────────────────────────────────────────┤${NC}"
        
        for service in "${services[@]}"; do
            local port="${service%%:*}"
            local name="${service##*:}"
            local status="checking"
            local color=$YELLOW
            
            # Try health endpoint
            local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost:$port/health" 2>/dev/null || echo "000")
            
            if [ "$response" = "200" ]; then
                status="Healthy"
                color=$GREEN
            elif [ "$response" = "000" ]; then
                status="Offline"
                color=$RED
                all_ok=false
            else
                status="HTTP $response"
                color=$YELLOW
            fi
            
            printf "  ${WHITE}│${NC}  %-20s %s%-10s${NC}  ${WHITE}│${NC}\n" "$name" "$color" "$status"
        done
        
        echo -e "  ${WHITE}├──────────────────────────────────────────┤${NC}"
        
        # Check observability
        local prom_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://localhost:9090/-/healthy" 2>/dev/null || echo "000")
        local graf_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://localhost:3000/api/health" 2>/dev/null || echo "000")
        
        printf "  ${WHITE}│${NC}  %-20s %s%-10s${NC}  ${WHITE}│${NC}\n" "Prometheus" \
            "$([ "$prom_status" = "200" ] && echo $GREEN || echo $YELLOW)" \
            "$([ "$prom_status" = "200" ] && echo "Healthy" || echo "HTTP $prom_status")"
        printf "  ${WHITE}│${NC}  %-20s %s%-10s${NC}  ${WHITE}│${NC}\n" "Grafana" \
            "$([ "$graf_status" = "200" ] && echo $GREEN || echo $YELLOW)" \
            "$([ "$graf_status" = "200" ] && echo "Healthy" || echo "HTTP $graf_status")"
        
        echo -e "  ${WHITE}└──────────────────────────────────────────┘${NC}"
    fi
    
    save_checkpoint "verification"
    clear_checkpoint  # Setup complete, clear checkpoint
    
    if [ "$all_ok" = true ]; then
        log SUCCESS "All verifications passed!"
    else
        log WARNING "Some services may still be starting. Check logs with:"
        echo -e "    ${CYAN}docker compose logs -f${NC}"
    fi
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}║   ${WHITE}${BOLD}🎉 NEXUS SETUP COMPLETE!${NC}${GREEN}                                    ║${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ "$SKIP_VENV" = false ]; then
        echo -e "  ${CYAN}Activate Environment:${NC}"
        echo -e "    ${WHITE}source venv/bin/activate${NC}"
        echo ""
    fi
    
    if [ "$SKIP_DOCKER" = false ]; then
        echo -e "  ${CYAN}Service URLs:${NC}"
        echo -e "    ${WHITE}Admin Dashboard:${NC}   http://localhost:8088"
        echo -e "    ${WHITE}Orchestrator API:${NC}  http://localhost:8080"
        echo -e "    ${WHITE}API Docs:${NC}          http://localhost:8080/docs"
        echo -e "    ${WHITE}Grafana:${NC}           http://localhost:3000 ${GRAY}(admin/nexus_admin)${NC}"
        echo -e "    ${WHITE}Prometheus:${NC}        http://localhost:9090"
        echo -e "    ${WHITE}Jaeger:${NC}            http://localhost:16686"
        echo ""
        
        echo -e "  ${CYAN}Quick Commands:${NC}"
        echo -e "    ${WHITE}docker compose -f infrastructure/docker/docker-compose.yml logs -f${NC}"
        echo -e "    ${WHITE}docker compose -f infrastructure/docker/docker-compose.yml ps${NC}"
        echo -e "    ${WHITE}./scripts/dev.sh help${NC}"
        echo ""
    fi
    
    echo -e "  ${CYAN}Documentation:${NC}"
    echo -e "    ${WHITE}docs/user_guide.md${NC}      - Getting started"
    echo -e "    ${WHITE}docs/architecture.md${NC}    - System design"
    echo -e "    ${WHITE}docs/testing.md${NC}         - Running tests"
    echo ""
    
    if [ -f "$ENV_FILE" ]; then
        echo -e "  ${YELLOW}⚠ Don't forget to update .env with your API credentials!${NC}"
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
    echo -e "${BOLD}Nexus Release Automation - Setup Script v2.3${NC}"
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./scripts/setup.sh [OPTIONS]"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --skip-docker     Skip Docker build and startup"
    echo "  --skip-venv       Skip Python virtual environment"
    echo "  --dev             Install development dependencies"
    echo "  --clean           Remove existing setup before installing"
    echo "  --resume          Resume from last checkpoint after failure"
    echo "  --verbose, -v     Show detailed output"
    echo "  --non-interactive Skip all prompts (use defaults)"
    echo "  --help, -h        Show this help message"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./scripts/setup.sh                    # Full setup"
    echo "  ./scripts/setup.sh --dev --verbose    # Dev setup with details"
    echo "  ./scripts/setup.sh --resume           # Continue after failure"
    echo "  ./scripts/setup.sh --skip-docker      # Python only"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-docker) SKIP_DOCKER=true; shift ;;
            --skip-venv) SKIP_VENV=true; shift ;;
            --dev) DEV_MODE=true; shift ;;
            --clean) CLEAN_MODE=true; shift ;;
            --resume) RESUME_MODE=true; shift ;;
            --verbose|-v) VERBOSE=true; shift ;;
            --non-interactive) NON_INTERACTIVE=true; shift ;;
            --help|-h) show_help; exit 0 ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Initialize
    > "$LOG_FILE"  # Clear log
    acquire_lock
    cd "$PROJECT_ROOT"
    
    # Show banner
    print_banner
    
    # Show resume info
    if [ "$RESUME_MODE" = true ]; then
        local checkpoint=$(get_checkpoint)
        if [ -n "$checkpoint" ]; then
            echo -e "  ${GREEN}Resuming from checkpoint:${NC} $checkpoint"
            echo ""
        else
            echo -e "  ${YELLOW}No checkpoint found. Starting fresh.${NC}"
            RESUME_MODE=false
        fi
    fi
    
    # Clear checkpoint if clean mode
    if [ "$CLEAN_MODE" = true ]; then
        clear_checkpoint
    fi
    
    # Record start time
    local start_time=$(date +%s)
    
    # Run setup stages
    check_prerequisites
    setup_virtualenv
    install_shared_lib
    install_dependencies
    setup_environment
    build_docker_images
    start_docker_services
    verify_setup
    
    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    echo ""
    log INFO "Setup completed in ${minutes}m ${seconds}s"
    
    # Print summary
    print_summary
}

# Run
main "$@"
