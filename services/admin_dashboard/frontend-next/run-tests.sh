#!/bin/bash

#############################################
#  Nexus Admin Dashboard - Test Runner
#  Interactive script for running all tests
#############################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions
print_header() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗               ║"
    echo "║   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝               ║"
    echo "║   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗               ║"
    echo "║   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║               ║"
    echo "║   ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║               ║"
    echo "║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝               ║"
    echo "║                                                              ║"
    echo "║           Admin Dashboard - Test Runner v1.0                 ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_menu() {
    echo -e "${WHITE}Select a test suite to run:${NC}"
    echo ""
    echo -e "  ${GREEN}[1]${NC}  Unit Tests (Vitest)"
    echo -e "  ${GREEN}[2]${NC}  Unit Tests - Watch Mode"
    echo -e "  ${GREEN}[3]${NC}  Unit Tests - UI Mode"
    echo -e "  ${GREEN}[4]${NC}  Unit Tests - Coverage Report"
    echo ""
    echo -e "  ${YELLOW}[5]${NC}  E2E Tests (Playwright)"
    echo -e "  ${YELLOW}[6]${NC}  E2E Tests - UI Mode"
    echo -e "  ${YELLOW}[7]${NC}  E2E Tests - Headed (visible browser)"
    echo -e "  ${YELLOW}[8]${NC}  E2E Tests - Specific File"
    echo ""
    echo -e "  ${MAGENTA}[9]${NC}  Run ALL Tests (Unit + E2E)"
    echo -e "  ${MAGENTA}[10]${NC} CI Mode (Unit + E2E + Coverage)"
    echo ""
    echo -e "  ${BLUE}[11]${NC} Install Dependencies"
    echo -e "  ${BLUE}[12]${NC} Install Playwright Browsers"
    echo ""
    echo -e "  ${RED}[0]${NC}  Exit"
    echo ""
    echo -n "Enter your choice: "
}

run_unit_tests() {
    echo -e "\n${GREEN}Running Unit Tests...${NC}\n"
    cd "$SCRIPT_DIR" && npm run test
}

run_unit_tests_watch() {
    echo -e "\n${GREEN}Running Unit Tests in Watch Mode...${NC}\n"
    cd "$SCRIPT_DIR" && npm run test:watch
}

run_unit_tests_ui() {
    echo -e "\n${GREEN}Starting Vitest UI...${NC}\n"
    cd "$SCRIPT_DIR" && npm run test:ui
}

run_unit_tests_coverage() {
    echo -e "\n${GREEN}Running Unit Tests with Coverage...${NC}\n"
    cd "$SCRIPT_DIR" && npm run test:coverage
}

run_e2e_tests() {
    echo -e "\n${YELLOW}Running E2E Tests...${NC}\n"
    cd "$SCRIPT_DIR" && npm run test:e2e
}

run_e2e_tests_ui() {
    echo -e "\n${YELLOW}Starting Playwright UI...${NC}\n"
    cd "$SCRIPT_DIR" && npm run test:e2e:ui
}

run_e2e_tests_headed() {
    echo -e "\n${YELLOW}Running E2E Tests with visible browser...${NC}\n"
    cd "$SCRIPT_DIR" && npx playwright test --headed
}

run_e2e_tests_file() {
    echo -e "\n${YELLOW}Available E2E test files:${NC}"
    ls -1 "$SCRIPT_DIR/e2e/"*.spec.ts 2>/dev/null | while read file; do
        echo "  - $(basename "$file")"
    done
    echo ""
    echo -n "Enter filename (e.g., auth.spec.ts): "
    read filename
    if [ -n "$filename" ]; then
        cd "$SCRIPT_DIR" && npx playwright test "e2e/$filename"
    fi
}

run_all_tests() {
    echo -e "\n${MAGENTA}Running ALL Tests...${NC}\n"
    cd "$SCRIPT_DIR" && npm run test:all
}

run_ci_tests() {
    echo -e "\n${MAGENTA}Running CI Tests (Unit + E2E + Coverage)...${NC}\n"
    cd "$SCRIPT_DIR" && npm run test:ci
}

install_deps() {
    echo -e "\n${BLUE}Installing dependencies...${NC}\n"
    cd "$SCRIPT_DIR" && npm install --legacy-peer-deps
}

install_playwright() {
    echo -e "\n${BLUE}Installing Playwright browsers...${NC}\n"
    cd "$SCRIPT_DIR" && npx playwright install
}

wait_for_key() {
    echo ""
    echo -e "${CYAN}Press any key to continue...${NC}"
    read -n 1 -s
}

# Main loop
while true; do
    print_header
    print_menu
    read choice

    case $choice in
        1) run_unit_tests; wait_for_key ;;
        2) run_unit_tests_watch ;;
        3) run_unit_tests_ui ;;
        4) run_unit_tests_coverage; wait_for_key ;;
        5) run_e2e_tests; wait_for_key ;;
        6) run_e2e_tests_ui ;;
        7) run_e2e_tests_headed; wait_for_key ;;
        8) run_e2e_tests_file; wait_for_key ;;
        9) run_all_tests; wait_for_key ;;
        10) run_ci_tests; wait_for_key ;;
        11) install_deps; wait_for_key ;;
        12) install_playwright; wait_for_key ;;
        0)
            echo -e "\n${GREEN}Goodbye!${NC}\n"
            exit 0
            ;;
        *)
            echo -e "\n${RED}Invalid option. Please try again.${NC}"
            sleep 1
            ;;
    esac
done
