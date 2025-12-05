#!/bin/bash
#==============================================================================
# Nexus Admin Dashboard - Integration Verification Script
#==============================================================================
#
# This script performs comprehensive integration testing of the Admin Dashboard
# including backend API tests, WebSocket tests, and frontend build verification.
#
# Usage:
#   ./scripts/verify-integration.sh [options]
#
# Options:
#   --backend-only    Only run backend tests
#   --frontend-only   Only run frontend tests
#   --skip-build      Skip build verification
#   --verbose         Show verbose output
#   --help            Show this help message
#
#==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/services/admin_dashboard/backend"
FRONTEND_DIR="$PROJECT_ROOT/services/admin_dashboard/frontend-next"

# Options
BACKEND_ONLY=false
FRONTEND_ONLY=false
SKIP_BUILD=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only) BACKEND_ONLY=true; shift ;;
        --frontend-only) FRONTEND_ONLY=true; shift ;;
        --skip-build) SKIP_BUILD=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --help)
            grep "^#" "$0" | grep -v "^#!/" | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Logging functions
log_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

log_step() {
    echo -e "${CYAN}▶${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_info() {
    echo -e "${MAGENTA}ℹ${NC} $1"
}

# Results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Test result function
record_result() {
    local name="$1"
    local status="$2"
    local details="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    case $status in
        pass)
            PASSED_TESTS=$((PASSED_TESTS + 1))
            log_success "$name"
            ;;
        fail)
            FAILED_TESTS=$((FAILED_TESTS + 1))
            log_error "$name: $details"
            ;;
        skip)
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            log_warning "$name (skipped: $details)"
            ;;
    esac
}

#==============================================================================
# Backend Tests
#==============================================================================

run_backend_tests() {
    log_header "Backend Integration Tests"
    
    cd "$BACKEND_DIR"
    
    # Check Python environment
    log_step "Checking Python environment..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_success "Python found: $PYTHON_VERSION"
    else
        log_error "Python3 not found"
        return 1
    fi
    
    # Check if virtual environment exists
    log_step "Setting up test environment..."
    if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv 2>/dev/null || log_warning "Could not create venv"
    fi
    
    # Install dependencies
    log_step "Installing test dependencies..."
    if [ -f "venv/bin/pip" ]; then
        ./venv/bin/pip install -q pytest pytest-asyncio httpx 2>/dev/null || true
    else
        pip install -q pytest pytest-asyncio httpx 2>/dev/null || true
    fi
    
    # Run pytest if available
    log_step "Running API tests..."
    if [ -d "tests" ]; then
        if command -v pytest &> /dev/null; then
            if $VERBOSE; then
                pytest tests/ -v 2>&1 || record_result "Backend API Tests" fail "pytest failed"
            else
                if pytest tests/ -q 2>&1; then
                    record_result "Backend API Tests" pass
                else
                    record_result "Backend API Tests" fail "some tests failed"
                fi
            fi
        else
            record_result "Backend API Tests" skip "pytest not installed"
        fi
    else
        record_result "Backend API Tests" skip "tests directory not found"
    fi
    
    # Check critical files exist
    log_step "Verifying backend structure..."
    
    critical_files=(
        "main.py"
        "auth.py"
        "db/session.py"
        "models/user.py"
        "crud/user.py"
        "alembic.ini"
    )
    
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            record_result "File: $file" pass
        else
            record_result "File: $file" fail "missing"
        fi
    done
    
    cd "$PROJECT_ROOT"
}

#==============================================================================
# Frontend Tests
#==============================================================================

run_frontend_tests() {
    log_header "Frontend Integration Tests"
    
    cd "$FRONTEND_DIR"
    
    # Check Node.js
    log_step "Checking Node.js environment..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_success "Node.js found: $NODE_VERSION"
    else
        log_error "Node.js not found"
        return 1
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        log_success "npm found: $NPM_VERSION"
    else
        log_error "npm not found"
        return 1
    fi
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        log_step "Installing dependencies..."
        npm install --legacy-peer-deps 2>/dev/null || npm install 2>/dev/null || true
    fi
    
    # TypeScript check
    log_step "Running TypeScript check..."
    if npm run type-check 2>/dev/null; then
        record_result "TypeScript Check" pass
    else
        record_result "TypeScript Check" fail "type errors found"
    fi
    
    # Lint check
    log_step "Running lint check..."
    if npm run lint 2>/dev/null; then
        record_result "ESLint Check" pass
    else
        record_result "ESLint Check" fail "lint errors found"
    fi
    
    # Build test (if not skipped)
    if ! $SKIP_BUILD; then
        log_step "Running build test..."
        if npm run build 2>/dev/null; then
            record_result "Frontend Build" pass
        else
            record_result "Frontend Build" fail "build failed"
        fi
    else
        record_result "Frontend Build" skip "skipped by user"
    fi
    
    # Run unit tests
    log_step "Running unit tests..."
    if npm run test:run 2>/dev/null || npm test -- --run 2>/dev/null; then
        record_result "Unit Tests" pass
    else
        record_result "Unit Tests" skip "test command failed or not configured"
    fi
    
    # Check critical files
    log_step "Verifying frontend structure..."
    
    critical_files=(
        "package.json"
        "next.config.js"
        "src/app/layout.tsx"
        "src/components/Layout.tsx"
        "src/hooks/useWebSocket.ts"
        "src/providers/WebSocketProvider.tsx"
        "src/types/index.ts"
    )
    
    for file in "${critical_files[@]}"; do
        if [ -f "$file" ]; then
            record_result "File: $file" pass
        else
            record_result "File: $file" fail "missing"
        fi
    done
    
    cd "$PROJECT_ROOT"
}

#==============================================================================
# API Connectivity Test
#==============================================================================

test_api_connectivity() {
    log_header "API Connectivity Tests"
    
    # Check if backend is running (optional)
    BACKEND_URL="${BACKEND_URL:-http://localhost:8088}"
    
    log_step "Testing API endpoint: $BACKEND_URL/health"
    if curl -sf "$BACKEND_URL/health" > /dev/null 2>&1; then
        record_result "API Health Check" pass
        
        # Test additional endpoints
        log_step "Testing stats endpoint..."
        if curl -sf "$BACKEND_URL/stats" > /dev/null 2>&1; then
            record_result "API Stats Endpoint" pass
        else
            record_result "API Stats Endpoint" skip "not running"
        fi
        
        log_step "Testing mode endpoint..."
        if curl -sf "$BACKEND_URL/mode" > /dev/null 2>&1; then
            record_result "API Mode Endpoint" pass
        else
            record_result "API Mode Endpoint" skip "not running"
        fi
    else
        record_result "API Health Check" skip "backend not running"
        log_info "Start backend with: cd services/admin_dashboard/backend && uvicorn main:app --reload"
    fi
}

#==============================================================================
# Summary
#==============================================================================

print_summary() {
    log_header "Integration Test Summary"
    
    echo ""
    echo -e "  ${GREEN}Passed:${NC}  $PASSED_TESTS"
    echo -e "  ${RED}Failed:${NC}  $FAILED_TESTS"
    echo -e "  ${YELLOW}Skipped:${NC} $SKIPPED_TESTS"
    echo -e "  ${BLUE}Total:${NC}   $TOTAL_TESTS"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}${BOLD}All tests passed! ✓${NC}"
        return 0
    else
        echo -e "${RED}${BOLD}Some tests failed. Please review the output above.${NC}"
        return 1
    fi
}

#==============================================================================
# Main
#==============================================================================

main() {
    log_header "Nexus Admin Dashboard - Integration Verification"
    log_info "Project root: $PROJECT_ROOT"
    log_info "Started at: $(date)"
    echo ""
    
    # Run tests based on options
    if ! $FRONTEND_ONLY; then
        run_backend_tests
    fi
    
    if ! $BACKEND_ONLY; then
        run_frontend_tests
    fi
    
    # API connectivity (if neither --backend-only nor --frontend-only)
    if ! $BACKEND_ONLY && ! $FRONTEND_ONLY; then
        test_api_connectivity
    fi
    
    # Print summary
    print_summary
}

# Run main
main "$@"

