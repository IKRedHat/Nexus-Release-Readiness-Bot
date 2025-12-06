#!/usr/bin/env bash
# ============================================================================
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║   🎯 NEXUS ADMIN DASHBOARD - QUICK DEMO SCRIPT v1.0                      ║
# ║                                                                           ║
# ║   One-command demo setup for the Nexus Admin Dashboard                   ║
# ║                                                                           ║
# ║   Features:                                                               ║
# ║     • Automatic dependency installation                                  ║
# ║     • Opens browser automatically                                        ║
# ║     • Works in Mock Mode (no backend needed)                             ║
# ║     • Colorful progress output                                           ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# Usage:
#   ./scripts/quick-demo.sh              # Frontend only (fastest)
#   ./scripts/quick-demo.sh --full       # Frontend + Backend
#   ./scripts/quick-demo.sh --help       # Show help
#
# ============================================================================

set -e

# ============================================================================
# COLORS & STYLING
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Emojis
CHECK="✅"
CROSS="❌"
ROCKET="🚀"
GEAR="⚙️"
PACKAGE="📦"
GLOBE="🌐"
CLOCK="⏱️"
SPARKLES="✨"
WARNING="⚠️"

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/services/admin_dashboard/frontend-next"
BACKEND_DIR="$PROJECT_ROOT/services/admin_dashboard/backend"

FRONTEND_PORT=3000
BACKEND_PORT=8088

MODE="frontend"  # Default: frontend only

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
    
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   🎯 NEXUS ADMIN DASHBOARD - QUICK DEMO                          ║
    ║                                                                   ║
    ║   Get up and running in under 2 minutes!                         ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝

EOF
    echo -e "${NC}"
}

log_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${WHITE}${BOLD}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

log_info() {
    echo -e "  ${CYAN}ℹ${NC}  $1"
}

log_success() {
    echo -e "  ${GREEN}${CHECK}${NC}  $1"
}

log_warning() {
    echo -e "  ${YELLOW}${WARNING}${NC}  $1"
}

log_error() {
    echo -e "  ${RED}${CROSS}${NC}  $1"
}

spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf "  ${CYAN}%c${NC}  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

open_browser() {
    local url=$1
    
    sleep 2  # Wait for server to start
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$url" 2>/dev/null || true
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$url" 2>/dev/null || sensible-browser "$url" 2>/dev/null || true
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        start "$url" 2>/dev/null || true
    fi
}

show_help() {
    echo -e "${CYAN}Nexus Admin Dashboard - Quick Demo Script${NC}"
    echo ""
    echo -e "${WHITE}Usage:${NC}"
    echo "  ./scripts/quick-demo.sh [OPTIONS]"
    echo ""
    echo -e "${WHITE}Options:${NC}"
    echo "  --frontend    Start frontend only (default, fastest)"
    echo "  --full        Start frontend + backend"
    echo "  --backend     Start backend only"
    echo "  --help        Show this help message"
    echo ""
    echo -e "${WHITE}Examples:${NC}"
    echo "  ./scripts/quick-demo.sh              # Quick frontend demo"
    echo "  ./scripts/quick-demo.sh --full       # Full stack demo"
    echo ""
    echo -e "${WHITE}URLs:${NC}"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8088"
    echo "  API Docs:  http://localhost:8088/docs"
    echo ""
}

# ============================================================================
# PREREQUISITE CHECKS
# ============================================================================

check_prerequisites() {
    log_step "${GEAR} Checking Prerequisites"
    
    local all_good=true
    
    # Node.js
    if check_command node; then
        local node_version=$(node --version)
        log_success "Node.js: ${node_version}"
    else
        log_error "Node.js is not installed"
        log_info "Install from: https://nodejs.org/"
        all_good=false
    fi
    
    # npm
    if check_command npm; then
        local npm_version=$(npm --version)
        log_success "npm: v${npm_version}"
    else
        log_error "npm is not installed"
        all_good=false
    fi
    
    # Python (only for full mode)
    if [[ "$MODE" == "full" ]] || [[ "$MODE" == "backend" ]]; then
        if check_command python3; then
            local python_version=$(python3 --version)
            log_success "Python: ${python_version}"
        else
            log_error "Python 3 is not installed (needed for backend)"
            log_info "Install from: https://python.org/"
            all_good=false
        fi
    fi
    
    # Check directories exist
    if [[ -d "$FRONTEND_DIR" ]]; then
        log_success "Frontend directory found"
    else
        log_error "Frontend directory not found: $FRONTEND_DIR"
        all_good=false
    fi
    
    if [[ "$MODE" == "full" ]] || [[ "$MODE" == "backend" ]]; then
        if [[ -d "$BACKEND_DIR" ]]; then
            log_success "Backend directory found"
        else
            log_error "Backend directory not found: $BACKEND_DIR"
            all_good=false
        fi
    fi
    
    if [[ "$all_good" == false ]]; then
        echo ""
        log_error "Prerequisites check failed. Please install missing dependencies."
        exit 1
    fi
    
    log_success "All prerequisites met!"
}

# ============================================================================
# FRONTEND SETUP
# ============================================================================

setup_frontend() {
    log_step "${PACKAGE} Setting Up Frontend"
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [[ -d "node_modules" ]]; then
        log_success "Dependencies already installed"
    else
        log_info "Installing dependencies (this may take a minute)..."
        npm install --silent &
        spinner $!
        log_success "Dependencies installed"
    fi
}

start_frontend() {
    log_step "${ROCKET} Starting Frontend Server"
    
    cd "$FRONTEND_DIR"
    
    # Check if port is in use
    if lsof -i :$FRONTEND_PORT &>/dev/null; then
        log_warning "Port $FRONTEND_PORT is already in use"
        log_info "Trying to use existing server..."
    else
        log_info "Starting Next.js development server..."
        
        # Start in background
        npm run dev &>/dev/null &
        FRONTEND_PID=$!
        
        # Wait for server to be ready
        local max_wait=30
        local waited=0
        while ! curl -s "http://localhost:$FRONTEND_PORT" &>/dev/null; do
            sleep 1
            waited=$((waited + 1))
            printf "  ${CYAN}⏳${NC}  Waiting for server... (${waited}s)\r"
            if [[ $waited -ge $max_wait ]]; then
                log_error "Server failed to start within ${max_wait}s"
                exit 1
            fi
        done
        echo ""
        log_success "Frontend server started (PID: $FRONTEND_PID)"
    fi
}

# ============================================================================
# BACKEND SETUP
# ============================================================================

setup_backend() {
    log_step "${PACKAGE} Setting Up Backend"
    
    cd "$BACKEND_DIR"
    
    # Create virtual environment if needed
    if [[ ! -d "venv" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_success "Virtual environment exists"
    fi
    
    # Activate and install dependencies
    source venv/bin/activate
    
    log_info "Installing Python dependencies..."
    pip install -q -r requirements.txt 2>/dev/null &
    spinner $!
    log_success "Dependencies installed"
}

start_backend() {
    log_step "${ROCKET} Starting Backend Server"
    
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # Check if port is in use
    if lsof -i :$BACKEND_PORT &>/dev/null; then
        log_warning "Port $BACKEND_PORT is already in use"
        log_info "Using existing server..."
    else
        log_info "Starting FastAPI server..."
        
        # Start in background
        uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload &>/dev/null &
        BACKEND_PID=$!
        
        # Wait for server to be ready
        local max_wait=20
        local waited=0
        while ! curl -s "http://localhost:$BACKEND_PORT/health" &>/dev/null; do
            sleep 1
            waited=$((waited + 1))
            printf "  ${CYAN}⏳${NC}  Waiting for server... (${waited}s)\r"
            if [[ $waited -ge $max_wait ]]; then
                log_error "Server failed to start within ${max_wait}s"
                exit 1
            fi
        done
        echo ""
        log_success "Backend server started (PID: $BACKEND_PID)"
    fi
}

# ============================================================================
# SUCCESS MESSAGE
# ============================================================================

show_success() {
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}${BOLD}  ${SPARKLES} DEMO IS READY! ${SPARKLES}${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [[ "$MODE" == "frontend" ]] || [[ "$MODE" == "full" ]]; then
        echo -e "  ${GLOBE} ${WHITE}Frontend:${NC}  ${CYAN}http://localhost:${FRONTEND_PORT}${NC}"
    fi
    
    if [[ "$MODE" == "backend" ]] || [[ "$MODE" == "full" ]]; then
        echo -e "  ${GLOBE} ${WHITE}Backend:${NC}   ${CYAN}http://localhost:${BACKEND_PORT}${NC}"
        echo -e "  ${GLOBE} ${WHITE}API Docs:${NC}  ${CYAN}http://localhost:${BACKEND_PORT}/docs${NC}"
    fi
    
    echo ""
    echo -e "  ${YELLOW}Press Ctrl+C to stop the servers${NC}"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Open browser
    if [[ "$MODE" == "frontend" ]] || [[ "$MODE" == "full" ]]; then
        log_info "Opening browser..."
        open_browser "http://localhost:${FRONTEND_PORT}"
    fi
}

# ============================================================================
# CLEANUP
# ============================================================================

cleanup() {
    echo ""
    log_info "Shutting down servers..."
    
    if [[ -n "${FRONTEND_PID:-}" ]]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    if [[ -n "${BACKEND_PID:-}" ]]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    log_success "Cleanup complete. Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --full)
                MODE="full"
                shift
                ;;
            --frontend)
                MODE="frontend"
                shift
                ;;
            --backend)
                MODE="backend"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    print_banner
    
    echo -e "  ${WHITE}Mode:${NC} ${CYAN}${MODE}${NC}"
    echo ""
    
    check_prerequisites
    
    if [[ "$MODE" == "frontend" ]] || [[ "$MODE" == "full" ]]; then
        setup_frontend
        start_frontend
    fi
    
    if [[ "$MODE" == "backend" ]] || [[ "$MODE" == "full" ]]; then
        setup_backend
        start_backend
    fi
    
    show_success
    
    # Keep script running
    while true; do
        sleep 1
    done
}

main "$@"

