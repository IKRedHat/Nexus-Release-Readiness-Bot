#!/usr/bin/env bash
#
# Nexus Release Automation - Development Helper Script
# Quick commands for common development tasks
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

cd "$PROJECT_ROOT"

show_help() {
    echo ""
    echo -e "${PURPLE}${BOLD}Nexus Development Helper v2.3${NC}"
    echo ""
    echo -e "${CYAN}Usage:${NC} ./scripts/dev.sh <command>"
    echo ""
    echo -e "${CYAN}Docker Commands:${NC}"
    echo "  start           Start all Docker services"
    echo "  stop            Stop all Docker services"
    echo "  restart         Restart all Docker services"
    echo "  logs            Follow Docker logs"
    echo "  logs <service>  Follow logs for specific service"
    echo "  status          Show service status"
    echo "  health          Run health checks"
    echo "  clean           Remove containers and volumes"
    echo "  rebuild         Rebuild and restart services"
    echo ""
    echo -e "${CYAN}Testing Commands:${NC}"
    echo "  test            Run all tests"
    echo "  test-unit       Run unit tests only"
    echo "  test-e2e        Run e2e tests only"
    echo "  lint            Run linters"
    echo "  format          Format code"
    echo ""
    echo -e "${CYAN}API Commands:${NC}"
    echo "  query <text>    Send a query to orchestrator"
    echo "  hygiene <proj>  Run hygiene check for project"
    echo "  rca <job> <num> Analyze build failure (RCA)"
    echo "  analytics       Get analytics KPIs"
    echo "  mode [mock|live] Get or set system mode"
    echo ""
    echo -e "${CYAN}Other Commands:${NC}"
    echo "  shell           Open Python shell with nexus_lib"
    echo "  admin           Open Admin Dashboard in browser"
    echo "  grafana         Open Grafana in browser"
    echo "  sync-labels     Sync GitHub labels"
    echo ""
}

activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    fi
}

case "${1:-help}" in
    start)
        echo -e "${CYAN}Starting services...${NC}"
        docker compose up -d
        echo -e "${GREEN}Services started!${NC}"
        ;;
    
    stop)
        echo -e "${CYAN}Stopping services...${NC}"
        docker compose down
        echo -e "${GREEN}Services stopped!${NC}"
        ;;
    
    restart)
        echo -e "${CYAN}Restarting services...${NC}"
        docker compose restart
        echo -e "${GREEN}Services restarted!${NC}"
        ;;
    
    logs)
        if [ -n "$2" ]; then
            docker compose logs -f "$2"
        else
            docker compose logs -f
        fi
        ;;
    
    status)
        docker compose ps
        ;;
    
    health)
        "$SCRIPT_DIR/verify.sh"
        ;;
    
    test)
        activate_venv
        echo -e "${CYAN}Running all tests...${NC}"
        pytest tests/ -v
        ;;
    
    test-unit)
        activate_venv
        echo -e "${CYAN}Running unit tests...${NC}"
        pytest tests/unit/ -v
        ;;
    
    test-e2e)
        activate_venv
        echo -e "${CYAN}Running e2e tests...${NC}"
        pytest tests/e2e/ -v
        ;;
    
    lint)
        activate_venv
        echo -e "${CYAN}Running linters...${NC}"
        echo "  Checking with flake8..."
        flake8 shared/ services/ --max-line-length=120 --ignore=E501,W503 || true
        echo "  Checking with mypy..."
        mypy shared/ --ignore-missing-imports || true
        echo -e "${GREEN}Linting complete!${NC}"
        ;;
    
    format)
        activate_venv
        echo -e "${CYAN}Formatting code...${NC}"
        black shared/ services/ tests/
        isort shared/ services/ tests/
        echo -e "${GREEN}Formatting complete!${NC}"
        ;;
    
    shell)
        activate_venv
        echo -e "${CYAN}Opening Python shell...${NC}"
        python3 -c "
import sys
sys.path.insert(0, 'shared')
print('Nexus Development Shell')
print('nexus_lib is available for import')
print()
" 
        python3 -i -c "import sys; sys.path.insert(0, 'shared')"
        ;;
    
    query)
        if [ -z "$2" ]; then
            echo -e "${RED}Usage: ./scripts/dev.sh query \"your query here\"${NC}"
            exit 1
        fi
        echo -e "${CYAN}Sending query to orchestrator...${NC}"
        curl -s -X POST http://localhost:8080/query \
            -H "Content-Type: application/json" \
            -d "{\"query\": \"$2\"}" | python3 -m json.tool
        ;;
    
    hygiene)
        project="${2:-PROJ}"
        echo -e "${CYAN}Running hygiene check for $project...${NC}"
        curl -s -X POST http://localhost:8005/run-check \
            -H "Content-Type: application/json" \
            -d "{\"project_key\": \"$project\", \"notify\": false}" | python3 -m json.tool
        ;;
    
    rca)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo -e "${RED}Usage: ./scripts/dev.sh rca <job_name> <build_number>${NC}"
            echo -e "Example: ./scripts/dev.sh rca nexus-main 142"
            exit 1
        fi
        echo -e "${CYAN}Analyzing build failure: $2 #$3...${NC}"
        curl -s -X POST http://localhost:8006/analyze \
            -H "Content-Type: application/json" \
            -d "{\"job_name\": \"$2\", \"build_number\": $3, \"notify\": false}" | python3 -m json.tool
        ;;
    
    analytics)
        echo -e "${CYAN}Fetching analytics KPIs...${NC}"
        curl -s http://localhost:8086/api/v1/kpis?time_range=7d | python3 -m json.tool
        ;;
    
    mode)
        if [ -z "$2" ]; then
            echo -e "${CYAN}Current system mode:${NC}"
            curl -s http://localhost:8088/config | python3 -c "import sys, json; d=json.load(sys.stdin); print('Mode:', d.get('nexus:mode', 'mock'))"
        else
            if [ "$2" = "mock" ] || [ "$2" = "live" ]; then
                echo -e "${CYAN}Setting system mode to: $2...${NC}"
                curl -s -X POST http://localhost:8088/mode \
                    -H "Content-Type: application/json" \
                    -d "{\"mode\": \"$2\"}" | python3 -m json.tool
            else
                echo -e "${RED}Invalid mode. Use 'mock' or 'live'${NC}"
                exit 1
            fi
        fi
        ;;
    
    admin)
        echo -e "${CYAN}Opening Admin Dashboard...${NC}"
        if command -v open &> /dev/null; then
            open http://localhost:8088
        elif command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:8088
        else
            echo "Visit: http://localhost:8088"
        fi
        ;;
    
    grafana)
        echo -e "${CYAN}Opening Grafana...${NC}"
        if command -v open &> /dev/null; then
            open http://localhost:3000
        elif command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:3000
        else
            echo "Visit: http://localhost:3000 (admin/nexus_admin)"
        fi
        ;;
    
    sync-labels)
        activate_venv
        echo -e "${CYAN}Syncing GitHub labels...${NC}"
        if [ -z "$GITHUB_TOKEN" ]; then
            echo -e "${YELLOW}Set GITHUB_TOKEN environment variable first${NC}"
            exit 1
        fi
        python3 "$SCRIPT_DIR/sync_labels.py"
        ;;
    
    clean)
        echo -e "${YELLOW}This will remove all containers and volumes. Continue? [y/N]${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            docker compose down -v --remove-orphans
            echo -e "${GREEN}Cleaned!${NC}"
        fi
        ;;
    
    rebuild)
        echo -e "${CYAN}Rebuilding and restarting services...${NC}"
        docker compose down
        docker compose build --no-cache
        docker compose up -d
        echo -e "${GREEN}Services rebuilt and started!${NC}"
        ;;
    
    help|--help|-h|*)
        show_help
        ;;
esac

