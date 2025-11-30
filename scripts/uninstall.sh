#!/usr/bin/env bash
#
# Nexus Release Automation - Uninstall Script
# Removes all Nexus components and cleans up
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

echo ""
echo -e "${YELLOW}${BOLD}⚠️  Nexus Uninstall Script${NC}"
echo ""
echo "This will remove:"
echo "  • Docker containers and images"
echo "  • Docker volumes (database data)"
echo "  • Python virtual environment"
echo "  • Generated files (.env, logs)"
echo ""
echo -e "${RED}This action cannot be undone!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

cd "$PROJECT_ROOT"

echo ""
echo -e "${CYAN}Stopping and removing Docker resources...${NC}"
docker compose down -v --remove-orphans --rmi local 2>/dev/null || true

echo -e "${CYAN}Removing virtual environment...${NC}"
rm -rf "$PROJECT_ROOT/venv"

echo -e "${CYAN}Removing generated files...${NC}"
rm -f "$PROJECT_ROOT/.env"
rm -f "$PROJECT_ROOT/setup.log"
rm -rf "$PROJECT_ROOT/__pycache__"
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

echo ""
echo -e "${GREEN}${BOLD}✓ Nexus has been uninstalled${NC}"
echo ""
echo "To reinstall, run:"
echo -e "  ${CYAN}./scripts/setup.sh${NC}"
echo ""

