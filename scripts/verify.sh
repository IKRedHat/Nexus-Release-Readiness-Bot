#!/usr/bin/env bash
#
# Nexus Release Automation - Health Verification Script
# Quick script to verify all services are running correctly
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
echo -e "${CYAN}${BOLD}🔍 Nexus Service Health Check${NC}"
echo -e "${CYAN}════════════════════════════════════════${NC}"
echo ""

# Service definitions
declare -A SERVICES=(
    ["Orchestrator"]="http://localhost:8080/health"
    ["Jira Agent"]="http://localhost:8081/health"
    ["Git/CI Agent"]="http://localhost:8082/health"
    ["Reporting Agent"]="http://localhost:8083/health"
    ["Slack Agent"]="http://localhost:8084/health"
    ["Jira Hygiene Agent"]="http://localhost:8085/health"
    ["RCA Agent"]="http://localhost:8006/health"
    ["Analytics"]="http://localhost:8086/health"
    ["Webhooks"]="http://localhost:8087/health"
    ["Admin Dashboard"]="http://localhost:8088/health"
    ["Prometheus"]="http://localhost:9090/-/healthy"
    ["Grafana"]="http://localhost:3000/api/health"
    ["Redis"]="http://localhost:6379"
)

all_healthy=true

for service in "Orchestrator" "Jira Agent" "Git/CI Agent" "Reporting Agent" "Slack Agent" "Jira Hygiene Agent" "RCA Agent" "Analytics" "Webhooks" "Admin Dashboard" "Prometheus" "Grafana"; do
    url="${SERVICES[$service]}"
    printf "  %-20s " "$service"
    
    response=$(curl -s --max-time 5 -w "%{http_code}" -o /dev/null "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ Healthy${NC}"
    elif [ "$response" = "000" ]; then
        echo -e "${RED}✗ Not responding${NC}"
        all_healthy=false
    else
        echo -e "${YELLOW}⚠ HTTP $response${NC}"
        all_healthy=false
    fi
done

echo ""
echo -e "${CYAN}════════════════════════════════════════${NC}"

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}${BOLD}All services are healthy! ✓${NC}"
else
    echo -e "${YELLOW}${BOLD}Some services need attention${NC}"
    echo ""
    echo -e "  ${CYAN}Troubleshooting:${NC}"
    echo "    docker compose ps           # Check container status"
    echo "    docker compose logs -f      # View logs"
    echo "    docker compose restart      # Restart services"
fi
echo ""

