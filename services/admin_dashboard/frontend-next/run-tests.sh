#!/bin/bash

# =============================================================================
# NEXUS ADMIN DASHBOARD - COMPREHENSIVE TEST SUITE RUNNER
# =============================================================================
#
# Interactive script to run all tests for the Nexus Admin Dashboard frontend.
#
# Usage:
#   ./run-tests.sh           # Interactive menu
#   ./run-tests.sh --all     # Run all tests
#   ./run-tests.sh --unit    # Run unit tests only
#   ./run-tests.sh --e2e     # Run E2E tests only
#   ./run-tests.sh --ci      # CI mode (coverage + E2E)
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

print_header() {
    echo -e "\n${PURPLE}============================================================${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}============================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    if [ ! -f "package.json" ]; then
        print_error "package.json not found. Are you in the frontend-next directory?"
        exit 1
    fi
    
    if [ ! -d "node_modules" ]; then
        print_warning "node_modules not found. Installing dependencies..."
        npm install --legacy-peer-deps
    fi
    
    # Check for Vitest
    if ! npm list vitest &>/dev/null; then
        print_warning "Vitest not installed. Installing test dependencies..."
        npm install --legacy-peer-deps
    fi
    
    # Check for Playwright
    if ! npm list @playwright/test &>/dev/null; then
        print_warning "Playwright not installed. Installing..."
        npm install --legacy-peer-deps
        npx playwright install --with-deps chromium
    fi
    
    print_success "All dependencies checked"
}

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

run_unit_tests() {
    print_header "Running Unit Tests (Vitest)"
    npm run test
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        print_success "Unit tests passed!"
    else
        print_error "Unit tests failed!"
    fi
    return $exit_code
}

run_unit_tests_watch() {
    print_header "Running Unit Tests in Watch Mode"
    npm run test:watch
}

run_unit_tests_ui() {
    print_header "Running Unit Tests with UI"
    npm run test:ui
}

run_unit_tests_coverage() {
    print_header "Running Unit Tests with Coverage"
    npm run test:coverage
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        print_success "Coverage report generated in coverage/"
        echo ""
        print_info "Open coverage/index.html in your browser to view the report"
    fi
    return $exit_code
}

run_e2e_tests() {
    print_header "Running E2E Tests (Playwright)"
    
    # Check if dev server is running
    if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_info "Starting development server..."
    fi
    
    npm run test:e2e
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        print_success "E2E tests passed!"
    else
        print_error "E2E tests failed!"
        print_info "Check test-results/ for screenshots and traces"
    fi
    return $exit_code
}

run_e2e_tests_ui() {
    print_header "Running E2E Tests with UI"
    npm run test:e2e:ui
}

run_e2e_tests_headed() {
    print_header "Running E2E Tests in Headed Mode"
    npm run test:e2e:headed
}

run_all_tests() {
    print_header "Running All Tests"
    
    local unit_exit=0
    local e2e_exit=0
    
    run_unit_tests || unit_exit=$?
    run_e2e_tests || e2e_exit=$?
    
    echo ""
    print_header "Test Summary"
    
    if [ $unit_exit -eq 0 ]; then
        print_success "Unit Tests: PASSED"
    else
        print_error "Unit Tests: FAILED"
    fi
    
    if [ $e2e_exit -eq 0 ]; then
        print_success "E2E Tests: PASSED"
    else
        print_error "E2E Tests: FAILED"
    fi
    
    if [ $unit_exit -eq 0 ] && [ $e2e_exit -eq 0 ]; then
        echo ""
        print_success "All tests passed! ✨"
        return 0
    else
        echo ""
        print_error "Some tests failed. Please check the output above."
        return 1
    fi
}

run_ci_tests() {
    print_header "Running CI Test Suite"
    
    local coverage_exit=0
    local e2e_exit=0
    
    print_info "Running unit tests with coverage..."
    run_unit_tests_coverage || coverage_exit=$?
    
    print_info "Running E2E tests..."
    run_e2e_tests || e2e_exit=$?
    
    echo ""
    print_header "CI Test Summary"
    
    if [ $coverage_exit -eq 0 ]; then
        print_success "Unit Tests + Coverage: PASSED"
    else
        print_error "Unit Tests + Coverage: FAILED"
    fi
    
    if [ $e2e_exit -eq 0 ]; then
        print_success "E2E Tests: PASSED"
    else
        print_error "E2E Tests: FAILED"
    fi
    
    # Generate combined report
    echo ""
    print_info "Test artifacts:"
    echo "  - Coverage: coverage/index.html"
    echo "  - E2E Report: playwright-report/index.html"
    echo "  - E2E Results: test-results/e2e-results.json"
    
    if [ $coverage_exit -eq 0 ] && [ $e2e_exit -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

lint_code() {
    print_header "Running Linter"
    npm run lint
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        print_success "Linting passed!"
    else
        print_error "Linting failed!"
    fi
    return $exit_code
}

install_playwright_browsers() {
    print_header "Installing Playwright Browsers"
    npx playwright install --with-deps
    print_success "Playwright browsers installed"
}

show_test_report() {
    print_header "Opening Test Reports"
    
    if [ -f "coverage/index.html" ]; then
        print_info "Opening coverage report..."
        open coverage/index.html 2>/dev/null || xdg-open coverage/index.html 2>/dev/null || print_warning "Could not open coverage report automatically"
    fi
    
    if [ -f "playwright-report/index.html" ]; then
        print_info "Opening Playwright report..."
        open playwright-report/index.html 2>/dev/null || xdg-open playwright-report/index.html 2>/dev/null || print_warning "Could not open Playwright report automatically"
    fi
}

# =============================================================================
# INTERACTIVE MENU
# =============================================================================

show_menu() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║          🧪 NEXUS ADMIN DASHBOARD TEST SUITE 🧪              ║"
    echo "║                                                              ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║                                                              ║"
    echo "║   UNIT TESTS (Vitest)                                        ║"
    echo "║   ─────────────────────                                      ║"
    echo "║   1) Run unit tests                                          ║"
    echo "║   2) Run unit tests (watch mode)                             ║"
    echo "║   3) Run unit tests (with UI)                                ║"
    echo "║   4) Run unit tests (with coverage)                          ║"
    echo "║                                                              ║"
    echo "║   E2E TESTS (Playwright)                                     ║"
    echo "║   ───────────────────────                                    ║"
    echo "║   5) Run E2E tests                                           ║"
    echo "║   6) Run E2E tests (with UI)                                 ║"
    echo "║   7) Run E2E tests (headed browser)                          ║"
    echo "║                                                              ║"
    echo "║   ALL TESTS                                                  ║"
    echo "║   ─────────                                                  ║"
    echo "║   8) Run ALL tests (unit + E2E)                              ║"
    echo "║   9) Run CI test suite (coverage + E2E)                      ║"
    echo "║                                                              ║"
    echo "║   UTILITIES                                                  ║"
    echo "║   ─────────                                                  ║"
    echo "║   l) Run linter                                              ║"
    echo "║   i) Install Playwright browsers                             ║"
    echo "║   r) Open test reports                                       ║"
    echo "║   c) Check dependencies                                      ║"
    echo "║                                                              ║"
    echo "║   q) Quit                                                    ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -n "Enter your choice: "
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    # Handle command line arguments
    case "${1:-}" in
        --all)
            check_dependencies
            run_all_tests
            exit $?
            ;;
        --unit)
            check_dependencies
            run_unit_tests
            exit $?
            ;;
        --e2e)
            check_dependencies
            run_e2e_tests
            exit $?
            ;;
        --ci)
            check_dependencies
            run_ci_tests
            exit $?
            ;;
        --coverage)
            check_dependencies
            run_unit_tests_coverage
            exit $?
            ;;
        --lint)
            lint_code
            exit $?
            ;;
        --help|-h)
            echo "Nexus Admin Dashboard Test Suite"
            echo ""
            echo "Usage: $0 [option]"
            echo ""
            echo "Options:"
            echo "  --all       Run all tests (unit + E2E)"
            echo "  --unit      Run unit tests only"
            echo "  --e2e       Run E2E tests only"
            echo "  --ci        CI mode (coverage + E2E)"
            echo "  --coverage  Run unit tests with coverage"
            echo "  --lint      Run linter"
            echo "  --help      Show this help message"
            echo ""
            echo "Without options, starts interactive menu."
            exit 0
            ;;
    esac
    
    # Interactive mode
    while true; do
        show_menu
        read choice
        
        case $choice in
            1) run_unit_tests; echo "Press Enter to continue..."; read ;;
            2) run_unit_tests_watch ;;
            3) run_unit_tests_ui ;;
            4) run_unit_tests_coverage; echo "Press Enter to continue..."; read ;;
            5) run_e2e_tests; echo "Press Enter to continue..."; read ;;
            6) run_e2e_tests_ui ;;
            7) run_e2e_tests_headed ;;
            8) run_all_tests; echo "Press Enter to continue..."; read ;;
            9) run_ci_tests; echo "Press Enter to continue..."; read ;;
            l|L) lint_code; echo "Press Enter to continue..."; read ;;
            i|I) install_playwright_browsers; echo "Press Enter to continue..."; read ;;
            r|R) show_test_report; echo "Press Enter to continue..."; read ;;
            c|C) check_dependencies; echo "Press Enter to continue..."; read ;;
            q|Q) echo "Goodbye!"; exit 0 ;;
            *) print_error "Invalid option. Please try again."; sleep 1 ;;
        esac
    done
}

main "$@"

