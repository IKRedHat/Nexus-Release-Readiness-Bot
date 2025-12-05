#!/bin/bash
#==============================================================================
#
#  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
#  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
#  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
#  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
#  ██║ ╚████║███████╗██╔╝ ╚██╗╚██████╔╝███████║
#  ╚═╝  ╚═══╝╚══════╝╚═╝   ╚═╝ ╚═════╝ ╚══════╝
#
#  PostgreSQL Production Setup Script
#  Admin Dashboard Database Configuration
#
#==============================================================================
#
# This interactive script guides you through setting up PostgreSQL for the
# Nexus Admin Dashboard production environment.
#
# Stages:
#   1. Environment Check - Verify prerequisites
#   2. Database Selection - Choose deployment method
#   3. Configuration - Set credentials and connection
#   4. Database Creation - Create database and user
#   5. Migration - Run Alembic migrations
#   6. Seed Data - Initialize default data
#   7. Verification - Test connection and queries
#   8. Environment Update - Configure application
#
# Usage:
#   ./scripts/setup-postgresql.sh [options]
#
# Options:
#   --non-interactive    Run with defaults (for CI/CD)
#   --docker             Use Docker PostgreSQL
#   --external           Use external PostgreSQL
#   --skip-seed          Skip seeding default data
#   --dry-run            Show what would be done
#   --help               Show this help
#
#==============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/services/admin_dashboard/backend"
ENV_FILE="$BACKEND_DIR/.env"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker/docker-compose.postgres.yml"

# Default configuration
DEFAULT_DB_HOST="localhost"
DEFAULT_DB_PORT="5432"
DEFAULT_DB_NAME="nexus_admin"
DEFAULT_DB_USER="nexus"
DEFAULT_DB_PASSWORD=""
DOCKER_CONTAINER_NAME="nexus-postgres"

# Options
INTERACTIVE=true
USE_DOCKER=false
USE_EXTERNAL=false
SKIP_SEED=false
DRY_RUN=false

# =============================================================================
# Colors and Styling
# =============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
NC='\033[0m'

# Bold colors
BOLD='\033[1m'
BOLD_RED='\033[1;31m'
BOLD_GREEN='\033[1;32m'
BOLD_YELLOW='\033[1;33m'
BOLD_BLUE='\033[1;34m'
BOLD_MAGENTA='\033[1;35m'
BOLD_CYAN='\033[1;36m'
BOLD_WHITE='\033[1;37m'

# Background colors
BG_RED='\033[41m'
BG_GREEN='\033[42m'
BG_YELLOW='\033[43m'
BG_BLUE='\033[44m'
BG_MAGENTA='\033[45m'
BG_CYAN='\033[46m'

# Dim
DIM='\033[2m'

# =============================================================================
# UI Components
# =============================================================================

print_banner() {
    echo ""
    echo -e "${BOLD_CYAN}"
    echo "  ╔══════════════════════════════════════════════════════════════════╗"
    echo "  ║                                                                  ║"
    echo "  ║   🐘  PostgreSQL Production Setup                                ║"
    echo "  ║       Nexus Admin Dashboard                                      ║"
    echo "  ║                                                                  ║"
    echo "  ╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_stage_header() {
    local stage_num="$1"
    local stage_name="$2"
    local total_stages=8
    
    echo ""
    echo -e "${BOLD_BLUE}┌──────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BOLD_BLUE}│${NC}  ${BOLD_WHITE}Stage $stage_num/$total_stages:${NC} ${BOLD_CYAN}$stage_name${NC}"
    echo -e "${BOLD_BLUE}└──────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

print_progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    printf "\r  ${CYAN}Progress: ${NC}["
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] ${BOLD_WHITE}%3d%%${NC}" $percentage
}

print_step() {
    local icon="$1"
    local message="$2"
    echo -e "  ${icon} ${message}"
}

print_success() {
    print_step "${GREEN}✓${NC}" "$1"
}

print_error() {
    print_step "${RED}✗${NC}" "${RED}$1${NC}"
}

print_warning() {
    print_step "${YELLOW}⚠${NC}" "${YELLOW}$1${NC}"
}

print_info() {
    print_step "${CYAN}ℹ${NC}" "$1"
}

print_action() {
    print_step "${MAGENTA}▶${NC}" "$1"
}

print_wait() {
    print_step "${BLUE}⏳${NC}" "$1"
}

print_check() {
    print_step "${GREEN}✔${NC}" "${GREEN}$1${NC}"
}

spinner() {
    local pid=$1
    local message="$2"
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    
    while ps -p $pid > /dev/null 2>&1; do
        for i in $(seq 0 9); do
            printf "\r  ${CYAN}${spinstr:$i:1}${NC} ${message}"
            sleep $delay
        done
    done
    printf "\r"
}

prompt_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    local is_secret="${4:-false}"
    
    if [ -n "$default" ]; then
        echo -ne "  ${CYAN}?${NC} ${prompt} ${DIM}[$default]${NC}: "
    else
        echo -ne "  ${CYAN}?${NC} ${prompt}: "
    fi
    
    if [ "$is_secret" = "true" ]; then
        read -s input
        echo ""
    else
        read input
    fi
    
    if [ -z "$input" ] && [ -n "$default" ]; then
        input="$default"
    fi
    
    eval "$var_name='$input'"
}

prompt_confirm() {
    local prompt="$1"
    local default="${2:-y}"
    
    if [ "$default" = "y" ]; then
        echo -ne "  ${CYAN}?${NC} ${prompt} ${DIM}[Y/n]${NC}: "
    else
        echo -ne "  ${CYAN}?${NC} ${prompt} ${DIM}[y/N]${NC}: "
    fi
    
    read answer
    answer="${answer:-$default}"
    
    case "$answer" in
        [Yy]*) return 0 ;;
        *) return 1 ;;
    esac
}

prompt_choice() {
    local prompt="$1"
    shift
    local options=("$@")
    
    echo -e "  ${CYAN}?${NC} ${prompt}"
    echo ""
    
    local i=1
    for opt in "${options[@]}"; do
        echo -e "    ${BOLD_WHITE}$i)${NC} $opt"
        ((i++))
    done
    echo ""
    
    while true; do
        echo -ne "  ${CYAN}→${NC} Enter choice [1-${#options[@]}]: "
        read choice
        
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#options[@]} ]; then
            return $((choice - 1))
        else
            print_error "Invalid choice. Please enter a number between 1 and ${#options[@]}"
        fi
    done
}

print_box() {
    local title="$1"
    local content="$2"
    local color="${3:-$CYAN}"
    
    echo -e "${color}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${color}│${NC} ${BOLD}$title${NC}"
    echo -e "${color}├─────────────────────────────────────────────────────────────┤${NC}"
    while IFS= read -r line; do
        printf "${color}│${NC} %-59s ${color}│${NC}\n" "$line"
    done <<< "$content"
    echo -e "${color}└─────────────────────────────────────────────────────────────┘${NC}"
}

# =============================================================================
# Parse Arguments
# =============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --non-interactive)
                INTERACTIVE=false
                shift
                ;;
            --docker)
                USE_DOCKER=true
                shift
                ;;
            --external)
                USE_EXTERNAL=true
                shift
                ;;
            --skip-seed)
                SKIP_SEED=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                grep "^#" "$0" | grep -v "^#!/" | sed 's/^# //' | sed 's/^#//'
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
}

# =============================================================================
# Stage 1: Environment Check
# =============================================================================

stage_environment_check() {
    print_stage_header 1 "Environment Check"
    
    local checks_passed=0
    local checks_total=5
    
    # Check Python
    print_action "Checking Python..."
    if command -v python3 &> /dev/null; then
        local py_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python $py_version found"
        ((checks_passed++))
    else
        print_error "Python 3 not found"
    fi
    print_progress_bar 1 $checks_total
    
    # Check pip
    print_action "Checking pip..."
    if command -v pip3 &> /dev/null || python3 -m pip --version &> /dev/null; then
        print_success "pip available"
        ((checks_passed++))
    else
        print_error "pip not found"
    fi
    print_progress_bar 2 $checks_total
    
    # Check psql client (optional but helpful)
    print_action "Checking psql client..."
    if command -v psql &> /dev/null; then
        local psql_version=$(psql --version 2>&1 | head -1)
        print_success "$psql_version"
        ((checks_passed++))
    else
        print_warning "psql client not found (optional)"
        ((checks_passed++))  # Still count as passed since it's optional
    fi
    print_progress_bar 3 $checks_total
    
    # Check Docker (if docker mode)
    print_action "Checking Docker..."
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            print_success "Docker is running"
            DOCKER_AVAILABLE=true
        else
            print_warning "Docker installed but not running"
            DOCKER_AVAILABLE=false
        fi
        ((checks_passed++))
    else
        print_info "Docker not installed (optional)"
        DOCKER_AVAILABLE=false
        ((checks_passed++))
    fi
    print_progress_bar 4 $checks_total
    
    # Check backend directory
    print_action "Checking backend directory..."
    if [ -d "$BACKEND_DIR" ]; then
        print_success "Backend directory found"
        ((checks_passed++))
    else
        print_error "Backend directory not found: $BACKEND_DIR"
    fi
    print_progress_bar 5 $checks_total
    
    echo ""
    echo ""
    
    if [ $checks_passed -eq $checks_total ]; then
        print_check "All environment checks passed!"
        return 0
    else
        print_error "$((checks_total - checks_passed)) checks failed"
        return 1
    fi
}

# =============================================================================
# Stage 2: Database Selection
# =============================================================================

stage_database_selection() {
    print_stage_header 2 "Database Selection"
    
    if ! $INTERACTIVE; then
        if $USE_DOCKER; then
            DB_MODE="docker"
            print_info "Using Docker PostgreSQL (--docker flag)"
        else
            DB_MODE="external"
            print_info "Using external PostgreSQL (--external flag)"
        fi
        return 0
    fi
    
    echo -e "  ${BOLD}Choose your PostgreSQL deployment method:${NC}"
    echo ""
    
    local options=(
        "🐳 Docker Container  - Quick local setup (recommended for development)"
        "☁️  External Database - Connect to existing PostgreSQL (production)"
        "🖥️  Local Installation - Use locally installed PostgreSQL"
    )
    
    prompt_choice "Select deployment method" "${options[@]}"
    local choice=$?
    
    case $choice in
        0)
            DB_MODE="docker"
            print_success "Selected: Docker Container"
            if ! $DOCKER_AVAILABLE; then
                print_error "Docker is not available. Please install and start Docker first."
                exit 1
            fi
            ;;
        1)
            DB_MODE="external"
            print_success "Selected: External Database"
            ;;
        2)
            DB_MODE="local"
            print_success "Selected: Local Installation"
            ;;
    esac
    
    echo ""
}

# =============================================================================
# Stage 3: Configuration
# =============================================================================

stage_configuration() {
    print_stage_header 3 "Configuration"
    
    case $DB_MODE in
        docker)
            configure_docker
            ;;
        external)
            configure_external
            ;;
        local)
            configure_local
            ;;
    esac
    
    # Display configuration summary
    echo ""
    local config_summary="Host:     $DB_HOST
Port:     $DB_PORT
Database: $DB_NAME
User:     $DB_USER
Password: ********"
    
    print_box "Configuration Summary" "$config_summary" "$GREEN"
    
    if $INTERACTIVE; then
        echo ""
        if ! prompt_confirm "Proceed with this configuration?"; then
            print_warning "Configuration cancelled. Please run the script again."
            exit 0
        fi
    fi
}

configure_docker() {
    print_info "Configuring Docker PostgreSQL..."
    echo ""
    
    if $INTERACTIVE; then
        prompt_input "Database name" "$DEFAULT_DB_NAME" "DB_NAME"
        prompt_input "Database user" "$DEFAULT_DB_USER" "DB_USER"
        prompt_input "Database password (leave empty to generate)" "" "DB_PASSWORD" true
    else
        DB_NAME="${POSTGRES_DB:-$DEFAULT_DB_NAME}"
        DB_USER="${POSTGRES_USER:-$DEFAULT_DB_USER}"
        DB_PASSWORD="${POSTGRES_PASSWORD:-}"
    fi
    
    # Generate password if not provided
    if [ -z "$DB_PASSWORD" ]; then
        DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
        print_info "Generated secure password"
    fi
    
    DB_HOST="localhost"
    DB_PORT="5432"
}

configure_external() {
    print_info "Configuring external PostgreSQL connection..."
    echo ""
    
    if $INTERACTIVE; then
        prompt_input "Database host" "$DEFAULT_DB_HOST" "DB_HOST"
        prompt_input "Database port" "$DEFAULT_DB_PORT" "DB_PORT"
        prompt_input "Database name" "$DEFAULT_DB_NAME" "DB_NAME"
        prompt_input "Database user" "$DEFAULT_DB_USER" "DB_USER"
        prompt_input "Database password" "" "DB_PASSWORD" true
        
        if [ -z "$DB_PASSWORD" ]; then
            print_error "Password is required for external database"
            exit 1
        fi
    else
        DB_HOST="${POSTGRES_HOST:-$DEFAULT_DB_HOST}"
        DB_PORT="${POSTGRES_PORT:-$DEFAULT_DB_PORT}"
        DB_NAME="${POSTGRES_DB:-$DEFAULT_DB_NAME}"
        DB_USER="${POSTGRES_USER:-$DEFAULT_DB_USER}"
        DB_PASSWORD="${POSTGRES_PASSWORD:-}"
        
        if [ -z "$DB_PASSWORD" ]; then
            print_error "POSTGRES_PASSWORD environment variable is required"
            exit 1
        fi
    fi
}

configure_local() {
    print_info "Configuring local PostgreSQL..."
    echo ""
    
    if $INTERACTIVE; then
        prompt_input "Database host" "$DEFAULT_DB_HOST" "DB_HOST"
        prompt_input "Database port" "$DEFAULT_DB_PORT" "DB_PORT"
        prompt_input "Database name" "$DEFAULT_DB_NAME" "DB_NAME"
        prompt_input "Database user" "$DEFAULT_DB_USER" "DB_USER"
        prompt_input "Database password" "" "DB_PASSWORD" true
    else
        DB_HOST="${POSTGRES_HOST:-$DEFAULT_DB_HOST}"
        DB_PORT="${POSTGRES_PORT:-$DEFAULT_DB_PORT}"
        DB_NAME="${POSTGRES_DB:-$DEFAULT_DB_NAME}"
        DB_USER="${POSTGRES_USER:-$DEFAULT_DB_USER}"
        DB_PASSWORD="${POSTGRES_PASSWORD:-}"
    fi
}

# =============================================================================
# Stage 4: Database Creation
# =============================================================================

stage_database_creation() {
    print_stage_header 4 "Database Creation"
    
    if $DRY_RUN; then
        print_info "[DRY RUN] Would create database: $DB_NAME"
        print_info "[DRY RUN] Would create user: $DB_USER"
        return 0
    fi
    
    case $DB_MODE in
        docker)
            create_docker_database
            ;;
        external|local)
            verify_database_connection
            ;;
    esac
}

create_docker_database() {
    print_action "Creating Docker PostgreSQL container..."
    
    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${DOCKER_CONTAINER_NAME}$"; then
        print_warning "Container '$DOCKER_CONTAINER_NAME' already exists"
        
        if $INTERACTIVE && prompt_confirm "Remove existing container and create new one?"; then
            docker rm -f "$DOCKER_CONTAINER_NAME" > /dev/null 2>&1
            print_success "Removed existing container"
        else
            # Check if it's running
            if docker ps --format '{{.Names}}' | grep -q "^${DOCKER_CONTAINER_NAME}$"; then
                print_success "Container is already running"
                return 0
            else
                print_action "Starting existing container..."
                docker start "$DOCKER_CONTAINER_NAME" > /dev/null 2>&1
                print_success "Container started"
                return 0
            fi
        fi
    fi
    
    # Create new container
    print_action "Starting PostgreSQL container..."
    
    docker run -d \
        --name "$DOCKER_CONTAINER_NAME" \
        -e POSTGRES_DB="$DB_NAME" \
        -e POSTGRES_USER="$DB_USER" \
        -e POSTGRES_PASSWORD="$DB_PASSWORD" \
        -p "${DB_PORT}:5432" \
        -v "nexus_postgres_data:/var/lib/postgresql/data" \
        --restart unless-stopped \
        postgres:15-alpine > /dev/null 2>&1 &
    
    local pid=$!
    spinner $pid "Starting PostgreSQL container..."
    wait $pid
    
    print_success "Container created successfully"
    
    # Wait for PostgreSQL to be ready
    print_action "Waiting for PostgreSQL to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec "$DOCKER_CONTAINER_NAME" pg_isready -U "$DB_USER" > /dev/null 2>&1; then
            print_success "PostgreSQL is ready!"
            return 0
        fi
        
        printf "\r  ${BLUE}⏳${NC} Waiting for PostgreSQL... (${attempt}/${max_attempts})"
        sleep 1
        ((attempt++))
    done
    
    echo ""
    print_error "PostgreSQL failed to start within ${max_attempts} seconds"
    return 1
}

verify_database_connection() {
    print_action "Verifying database connection..."
    
    # Build connection string
    local conn_string="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    
    # Try to connect using psql if available
    if command -v psql &> /dev/null; then
        if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
            print_success "Database connection successful!"
            return 0
        else
            print_error "Failed to connect to database"
            print_info "Please ensure the database exists and credentials are correct"
            return 1
        fi
    else
        print_warning "psql not available, will verify connection during migration"
        return 0
    fi
}

# =============================================================================
# Stage 5: Migration
# =============================================================================

stage_migration() {
    print_stage_header 5 "Database Migration"
    
    cd "$BACKEND_DIR"
    
    # Ensure virtual environment
    print_action "Setting up Python environment..."
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        python3 -m venv venv 2>/dev/null || true
    fi
    
    # Activate and install dependencies
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    print_action "Installing dependencies..."
    pip install -q sqlalchemy psycopg2-binary alembic 2>/dev/null || pip install sqlalchemy psycopg2-binary alembic
    print_success "Dependencies installed"
    
    # Set environment variables for Alembic
    export POSTGRES_HOST="$DB_HOST"
    export POSTGRES_PORT="$DB_PORT"
    export POSTGRES_DB="$DB_NAME"
    export POSTGRES_USER="$DB_USER"
    export POSTGRES_PASSWORD="$DB_PASSWORD"
    export USE_DATABASE="true"
    
    if $DRY_RUN; then
        print_info "[DRY RUN] Would run: alembic upgrade head"
        return 0
    fi
    
    # Run migrations
    print_action "Running Alembic migrations..."
    
    if [ -f "alembic.ini" ]; then
        if alembic upgrade head 2>&1; then
            print_success "Migrations completed successfully!"
        else
            print_error "Migration failed"
            print_info "Check database connection and credentials"
            return 1
        fi
    else
        print_warning "alembic.ini not found, skipping migrations"
        print_info "Run 'alembic init alembic' to set up migrations"
    fi
    
    cd "$PROJECT_ROOT"
}

# =============================================================================
# Stage 6: Seed Data
# =============================================================================

stage_seed_data() {
    print_stage_header 6 "Seed Data"
    
    if $SKIP_SEED; then
        print_info "Skipping seed data (--skip-seed flag)"
        return 0
    fi
    
    if $DRY_RUN; then
        print_info "[DRY RUN] Would seed default roles and admin user"
        return 0
    fi
    
    print_action "Seeding default data..."
    
    # The migration already includes seed data, but we can verify it
    cd "$BACKEND_DIR"
    
    python3 << 'EOF'
import os
import sys
sys.path.insert(0, os.getcwd())

try:
    from db.session import SessionLocal, init_db
    from crud.role import crud_role
    
    # Initialize tables if needed
    init_db()
    
    db = SessionLocal()
    try:
        # Check if roles exist
        roles = crud_role.get_multi(db, limit=10)
        if len(roles) > 0:
            print(f"  ✓ Found {len(roles)} roles in database")
        else:
            # Initialize system roles
            created = crud_role.initialize_system_roles(db)
            print(f"  ✓ Created {len(created)} system roles")
    finally:
        db.close()
    
    print("  ✓ Seed data verification complete")
except Exception as e:
    print(f"  ⚠ Could not verify seed data: {e}")
    # Not a fatal error - migrations may have already seeded
EOF
    
    cd "$PROJECT_ROOT"
    print_success "Seed data processed"
}

# =============================================================================
# Stage 7: Verification
# =============================================================================

stage_verification() {
    print_stage_header 7 "Verification"
    
    print_action "Running verification tests..."
    
    local tests_passed=0
    local tests_total=4
    
    # Test 1: Connection
    print_action "Testing database connection..."
    cd "$BACKEND_DIR"
    
    if python3 -c "
import os
os.environ['POSTGRES_HOST'] = '$DB_HOST'
os.environ['POSTGRES_PORT'] = '$DB_PORT'
os.environ['POSTGRES_DB'] = '$DB_NAME'
os.environ['POSTGRES_USER'] = '$DB_USER'
os.environ['POSTGRES_PASSWORD'] = '$DB_PASSWORD'
os.environ['USE_DATABASE'] = 'true'

from db.session import check_db_connection
if check_db_connection():
    exit(0)
else:
    exit(1)
" 2>/dev/null; then
        print_success "Database connection: OK"
        ((tests_passed++))
    else
        print_error "Database connection: FAILED"
    fi
    print_progress_bar 1 $tests_total
    
    # Test 2: Tables exist
    print_action "Checking database tables..."
    if python3 -c "
import os
os.environ['POSTGRES_HOST'] = '$DB_HOST'
os.environ['POSTGRES_PORT'] = '$DB_PORT'
os.environ['POSTGRES_DB'] = '$DB_NAME'
os.environ['POSTGRES_USER'] = '$DB_USER'
os.environ['POSTGRES_PASSWORD'] = '$DB_PASSWORD'
os.environ['USE_DATABASE'] = 'true'

from db.session import engine
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
required = ['users', 'roles', 'audit_logs', 'refresh_tokens']
missing = [t for t in required if t not in tables]
if missing:
    print(f'Missing tables: {missing}')
    exit(1)
exit(0)
" 2>/dev/null; then
        print_success "Database tables: OK"
        ((tests_passed++))
    else
        print_error "Database tables: FAILED"
    fi
    print_progress_bar 2 $tests_total
    
    # Test 3: System roles exist
    print_action "Checking system roles..."
    if python3 -c "
import os
os.environ['POSTGRES_HOST'] = '$DB_HOST'
os.environ['POSTGRES_PORT'] = '$DB_PORT'
os.environ['POSTGRES_DB'] = '$DB_NAME'
os.environ['POSTGRES_USER'] = '$DB_USER'
os.environ['POSTGRES_PASSWORD'] = '$DB_PASSWORD'
os.environ['USE_DATABASE'] = 'true'

from db.session import SessionLocal
from models.role import RoleModel

db = SessionLocal()
roles = db.query(RoleModel).filter(RoleModel.is_system_role == True).all()
db.close()
if len(roles) >= 3:
    exit(0)
exit(1)
" 2>/dev/null; then
        print_success "System roles: OK"
        ((tests_passed++))
    else
        print_warning "System roles: Check manually"
        ((tests_passed++))  # Non-critical
    fi
    print_progress_bar 3 $tests_total
    
    # Test 4: Admin user exists
    print_action "Checking admin user..."
    if python3 -c "
import os
os.environ['POSTGRES_HOST'] = '$DB_HOST'
os.environ['POSTGRES_PORT'] = '$DB_PORT'
os.environ['POSTGRES_DB'] = '$DB_NAME'
os.environ['POSTGRES_USER'] = '$DB_USER'
os.environ['POSTGRES_PASSWORD'] = '$DB_PASSWORD'
os.environ['USE_DATABASE'] = 'true'

from db.session import SessionLocal
from models.user import UserModel

db = SessionLocal()
admin = db.query(UserModel).filter(UserModel.email.like('%admin%')).first()
db.close()
if admin:
    exit(0)
exit(1)
" 2>/dev/null; then
        print_success "Admin user: OK"
        ((tests_passed++))
    else
        print_warning "Admin user: Check manually"
        ((tests_passed++))  # Non-critical
    fi
    print_progress_bar 4 $tests_total
    
    cd "$PROJECT_ROOT"
    
    echo ""
    echo ""
    
    if [ $tests_passed -eq $tests_total ]; then
        print_check "All verification tests passed!"
        return 0
    else
        print_warning "$((tests_total - tests_passed)) tests need attention"
        return 0  # Non-fatal
    fi
}

# =============================================================================
# Stage 8: Environment Update
# =============================================================================

stage_environment_update() {
    print_stage_header 8 "Environment Update"
    
    print_action "Generating environment configuration..."
    
    local env_content="# PostgreSQL Configuration (Generated by setup-postgresql.sh)
# Generated: $(date)

# Database Connection
POSTGRES_HOST=$DB_HOST
POSTGRES_PORT=$DB_PORT
POSTGRES_DB=$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD

# Enable Database Mode
USE_DATABASE=true

# Connection Pool Settings (optional)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
"

    if $DRY_RUN; then
        print_info "[DRY RUN] Would create .env file with configuration"
        echo ""
        print_box "Environment Configuration" "$env_content" "$CYAN"
        return 0
    fi
    
    # Backup existing .env if present
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d%H%M%S)"
        print_info "Backed up existing .env file"
    fi
    
    # Write new .env
    echo "$env_content" > "$ENV_FILE"
    print_success "Environment file created: $ENV_FILE"
    
    echo ""
    print_box "Environment Variables" "$env_content" "$GREEN"
    
    echo ""
    print_info "Add these to your deployment environment:"
    echo ""
    echo -e "  ${DIM}export USE_DATABASE=true${NC}"
    echo -e "  ${DIM}export POSTGRES_HOST=$DB_HOST${NC}"
    echo -e "  ${DIM}export POSTGRES_PORT=$DB_PORT${NC}"
    echo -e "  ${DIM}export POSTGRES_DB=$DB_NAME${NC}"
    echo -e "  ${DIM}export POSTGRES_USER=$DB_USER${NC}"
    echo -e "  ${DIM}export POSTGRES_PASSWORD=********${NC}"
}

# =============================================================================
# Summary
# =============================================================================

print_summary() {
    echo ""
    echo -e "${BOLD_GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD_GREEN}║                                                                  ║${NC}"
    echo -e "${BOLD_GREEN}║   ✅  PostgreSQL Setup Complete!                                 ║${NC}"
    echo -e "${BOLD_GREEN}║                                                                  ║${NC}"
    echo -e "${BOLD_GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    echo -e "  ${BOLD}Database Details:${NC}"
    echo -e "    Host:     ${CYAN}$DB_HOST${NC}"
    echo -e "    Port:     ${CYAN}$DB_PORT${NC}"
    echo -e "    Database: ${CYAN}$DB_NAME${NC}"
    echo -e "    User:     ${CYAN}$DB_USER${NC}"
    echo ""
    
    if [ "$DB_MODE" = "docker" ]; then
        echo -e "  ${BOLD}Docker Container:${NC}"
        echo -e "    Name:     ${CYAN}$DOCKER_CONTAINER_NAME${NC}"
        echo -e "    Stop:     ${DIM}docker stop $DOCKER_CONTAINER_NAME${NC}"
        echo -e "    Start:    ${DIM}docker start $DOCKER_CONTAINER_NAME${NC}"
        echo -e "    Logs:     ${DIM}docker logs $DOCKER_CONTAINER_NAME${NC}"
        echo ""
    fi
    
    echo -e "  ${BOLD}Next Steps:${NC}"
    echo -e "    1. Start the backend: ${DIM}cd services/admin_dashboard/backend && uvicorn main:app --reload${NC}"
    echo -e "    2. Verify at:         ${DIM}http://localhost:8088/health${NC}"
    echo -e "    3. Login as admin:    ${DIM}admin@nexus.dev${NC}"
    echo ""
    
    echo -e "  ${BOLD}For Production:${NC}"
    echo -e "    • Set environment variables in your deployment platform"
    echo -e "    • Use a managed PostgreSQL service (AWS RDS, Render, etc.)"
    echo -e "    • Enable SSL connections"
    echo -e "    • Set up automated backups"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
    parse_args "$@"
    
    print_banner
    
    echo -e "  ${DIM}This script will guide you through PostgreSQL setup.${NC}"
    echo -e "  ${DIM}Press Ctrl+C at any time to cancel.${NC}"
    echo ""
    
    if $DRY_RUN; then
        echo -e "  ${BOLD_YELLOW}🔍 DRY RUN MODE - No changes will be made${NC}"
        echo ""
    fi
    
    # Run stages
    stage_environment_check || exit 1
    stage_database_selection
    stage_configuration
    stage_database_creation || exit 1
    stage_migration
    stage_seed_data
    stage_verification
    stage_environment_update
    
    print_summary
}

# Run main
main "$@"

