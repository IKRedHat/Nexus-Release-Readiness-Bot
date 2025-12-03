#!/bin/bash
# ============================================================================
# Nexus API Test Script
# Tests all API endpoints across all services
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Test results storage
declare -a FAILURES

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                   ║"
    echo "║   🧪 NEXUS API TEST SUITE                                        ║"
    echo "║                                                                   ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_code="${5:-200}"
    
    # Make request
    if [ -n "$data" ]; then
        response=$(curl -s -o /tmp/nexus_response.txt -w "%{http_code}" \
            -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$data" \
            --max-time 10 2>/dev/null || echo "000")
    else
        response=$(curl -s -o /tmp/nexus_response.txt -w "%{http_code}" \
            -X "$method" "$url" \
            --max-time 10 2>/dev/null || echo "000")
    fi
    
    # Check result
    if [ "$response" = "$expected_code" ]; then
        printf "  ${GREEN}✓${NC} %-45s ${GREEN}%s${NC}\n" "$name" "$response"
        ((PASSED++))
        return 0
    elif [ "$response" = "000" ]; then
        printf "  ${RED}✗${NC} %-45s ${RED}Connection Failed${NC}\n" "$name"
        FAILURES+=("$name: Connection failed")
        ((FAILED++))
        return 1
    else
        printf "  ${RED}✗${NC} %-45s ${RED}%s (expected %s)${NC}\n" "$name" "$response" "$expected_code"
        FAILURES+=("$name: Got $response, expected $expected_code")
        ((FAILED++))
        return 1
    fi
}

section_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  ▶ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# MAIN TEST SUITE
# ============================================================================

print_banner

echo -e "${WHITE}Starting comprehensive API tests...${NC}"
echo -e "${WHITE}Testing $(date)${NC}"

# -----------------------------------------------------------------------------
# ORCHESTRATOR (8080)
# -----------------------------------------------------------------------------
section_header "Orchestrator API (Port 8080)"

test_endpoint "Health Check" "GET" "http://localhost:8080/health"
test_endpoint "Liveness Probe" "GET" "http://localhost:8080/live"
test_endpoint "Readiness Probe" "GET" "http://localhost:8080/ready"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8080/metrics"
test_endpoint "List Specialists" "GET" "http://localhost:8080/specialists"
test_endpoint "List All Tools" "GET" "http://localhost:8080/specialists/tools/all"
test_endpoint "Memory Stats" "GET" "http://localhost:8080/memory/stats"
test_endpoint "Query Endpoint" "POST" "http://localhost:8080/query" '{"query":"hello"}'

# -----------------------------------------------------------------------------
# JIRA AGENT (8081)
# -----------------------------------------------------------------------------
section_header "Jira Agent API (Port 8081)"

test_endpoint "Health Check" "GET" "http://localhost:8081/health"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8081/metrics"
test_endpoint "Execute Action" "POST" "http://localhost:8081/execute" '{"action":"get_ticket","parameters":{"ticket_key":"TEST-1"}}'
test_endpoint "Search Tickets" "GET" "http://localhost:8081/search?jql=project=TEST"

# -----------------------------------------------------------------------------
# GIT/CI AGENT (8082)
# -----------------------------------------------------------------------------
section_header "Git/CI Agent API (Port 8082)"

test_endpoint "Health Check" "GET" "http://localhost:8082/health"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8082/metrics"
test_endpoint "Execute Action" "POST" "http://localhost:8082/execute" '{"action":"get_repo_status","parameters":{}}'

# -----------------------------------------------------------------------------
# REPORTING AGENT (8083)
# -----------------------------------------------------------------------------
section_header "Reporting Agent API (Port 8083)"

test_endpoint "Health Check" "GET" "http://localhost:8083/health"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8083/metrics"
test_endpoint "Execute Action" "POST" "http://localhost:8083/execute" '{"action":"generate_report","parameters":{}}'

# -----------------------------------------------------------------------------
# SLACK AGENT (8084)
# -----------------------------------------------------------------------------
section_header "Slack Agent API (Port 8084)"

test_endpoint "Health Check" "GET" "http://localhost:8084/health"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8084/metrics"
test_endpoint "Execute Action" "POST" "http://localhost:8084/execute" '{"action":"send_message","parameters":{}}'

# -----------------------------------------------------------------------------
# JIRA HYGIENE AGENT (8085)
# -----------------------------------------------------------------------------
section_header "Jira Hygiene Agent API (Port 8085)"

test_endpoint "Health Check" "GET" "http://localhost:8085/health"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8085/metrics"
test_endpoint "Status Check" "GET" "http://localhost:8085/status"
test_endpoint "Execute Action" "POST" "http://localhost:8085/execute" '{"action":"run_check","parameters":{}}'

# -----------------------------------------------------------------------------
# RCA AGENT (8006)
# -----------------------------------------------------------------------------
section_header "RCA Agent API (Port 8006)"

test_endpoint "Health Check" "GET" "http://localhost:8006/health"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8006/metrics"
# Note: Execute requires valid job_name, so we test analyze endpoint directly
test_endpoint "Analyze (mock)" "POST" "http://localhost:8006/analyze" '{"job_name":"test-job","build_number":1}'

# -----------------------------------------------------------------------------
# ANALYTICS SERVICE (8086)
# -----------------------------------------------------------------------------
section_header "Analytics Service API (Port 8086)"

test_endpoint "Health Check" "GET" "http://localhost:8086/health"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8086/metrics"
test_endpoint "KPIs" "GET" "http://localhost:8086/api/v1/kpis"
test_endpoint "Trends" "GET" "http://localhost:8086/api/v1/trends"
test_endpoint "Insights" "GET" "http://localhost:8086/api/v1/insights"
test_endpoint "Teams" "GET" "http://localhost:8086/api/v1/teams"
test_endpoint "Anomalies" "GET" "http://localhost:8086/api/v1/anomalies"
test_endpoint "Data Sources" "GET" "http://localhost:8086/api/v1/sources"
# Benchmark requires parameters, testing that endpoint exists (422 = validation error is OK)
test_endpoint "Benchmark (endpoint exists)" "GET" "http://localhost:8086/api/v1/benchmark" "" "422"

# -----------------------------------------------------------------------------
# WEBHOOKS SERVICE (8087)
# -----------------------------------------------------------------------------
section_header "Webhooks Service API (Port 8087)"

test_endpoint "Health Check" "GET" "http://localhost:8087/health"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8087/metrics"
test_endpoint "Event Types" "GET" "http://localhost:8087/api/v1/event-types"
test_endpoint "Subscriptions" "GET" "http://localhost:8087/api/v1/subscriptions"
test_endpoint "Deliveries" "GET" "http://localhost:8087/api/v1/deliveries"
test_endpoint "Statistics" "GET" "http://localhost:8087/api/v1/stats"

# -----------------------------------------------------------------------------
# ADMIN DASHBOARD (8088)
# -----------------------------------------------------------------------------
section_header "Admin Dashboard API (Port 8088)"

test_endpoint "Health Check" "GET" "http://localhost:8088/health"
test_endpoint "Prometheus Metrics" "GET" "http://localhost:8088/metrics"
test_endpoint "System Mode" "GET" "http://localhost:8088/mode"
test_endpoint "Configuration" "GET" "http://localhost:8088/config"
# Config templates endpoint may not be implemented
# test_endpoint "Config Templates" "GET" "http://localhost:8088/config/templates"
test_endpoint "System Stats" "GET" "http://localhost:8088/stats"
test_endpoint "Health Overview" "GET" "http://localhost:8088/health-check"
test_endpoint "Aggregated Metrics" "GET" "http://localhost:8088/api/metrics"
test_endpoint "Releases List" "GET" "http://localhost:8088/releases"
test_endpoint "Release Calendar" "GET" "http://localhost:8088/releases/calendar"
# Release templates endpoint may not be implemented yet
# test_endpoint "Release Templates" "GET" "http://localhost:8088/releases/templates"

# -----------------------------------------------------------------------------
# OBSERVABILITY STACK
# -----------------------------------------------------------------------------
section_header "Observability Stack"

test_endpoint "Prometheus Health" "GET" "http://localhost:9090/-/healthy"
test_endpoint "Prometheus Ready" "GET" "http://localhost:9090/-/ready"
test_endpoint "Grafana Health" "GET" "http://localhost:3000/api/health"
test_endpoint "Jaeger UI" "GET" "http://localhost:16686/"

# ============================================================================
# RESULTS SUMMARY
# ============================================================================

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}  TEST RESULTS SUMMARY${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

TOTAL=$((PASSED + FAILED + SKIPPED))

echo -e "  Total Tests:    ${WHITE}$TOTAL${NC}"
echo -e "  Passed:         ${GREEN}$PASSED${NC}"
echo -e "  Failed:         ${RED}$FAILED${NC}"
echo -e "  Skipped:        ${YELLOW}$SKIPPED${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}${BOLD}  FAILURES:${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    for failure in "${FAILURES[@]}"; do
        echo -e "  ${RED}•${NC} $failure"
    done
    echo ""
fi

# Calculate pass rate
if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
else
    PASS_RATE=0
fi

if [ $PASS_RATE -eq 100 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}║   ✅ ALL TESTS PASSED! ($PASS_RATE%)                              ║${NC}"
    echo -e "${GREEN}║                                                                   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
elif [ $PASS_RATE -ge 80 ]; then
    echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║   ⚠️  MOSTLY PASSING ($PASS_RATE%)                                ║${NC}"
    echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ TESTS FAILING ($PASS_RATE%)                                  ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════════╝${NC}"
fi

echo ""
echo -e "${WHITE}Quick Links:${NC}"
echo -e "  • Swagger Docs:     ${CYAN}http://localhost:8080/docs${NC}"
echo -e "  • Admin Dashboard:  ${CYAN}http://localhost:8088${NC}"
echo -e "  • Grafana:          ${CYAN}http://localhost:3000${NC}"
echo ""

exit $FAILED

