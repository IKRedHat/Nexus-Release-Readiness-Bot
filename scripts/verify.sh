#!/usr/bin/env bash
# ============================================================================
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║   🔍 NEXUS RELEASE AUTOMATION - VERIFICATION SCRIPT v3.0                 ║
# ║                                                                           ║
# ║   Comprehensive health and verification checks                           ║
# ║                                                                           ║
# ║   Features:                                                               ║
# ║     • Parallel service health checks                                     ║
# ║     • Network connectivity verification                                  ║
# ║     • Docker resource status                                             ║
# ║     • Python environment validation                                      ║
# ║     • JSON/table output formats                                          ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# ============================================================================

# Script identification
NEXUS_SCRIPT_NAME="verify"
NEXUS_SCRIPT_VERSION="3.0.0"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source libraries
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/network.sh"
source "$SCRIPT_DIR/lib/docker.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

VENV_DIR="$NEXUS_PROJECT_ROOT/venv"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-table}"  # table, json, minimal
CHECK_TIMEOUT="${CHECK_TIMEOUT:-5}"

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Results array for JSON output
declare -a RESULTS=()

# ============================================================================
# OUTPUT UTILITIES
# ============================================================================

record_result() {
    local category="$1"
    local name="$2"
    local status="$3"
    local details="${4:-}"
    
    ((TOTAL_CHECKS++))
    
    case "$status" in
        pass|healthy|ok)
            ((PASSED_CHECKS++))
            status="pass"
            ;;
        fail|unhealthy|error)
            ((FAILED_CHECKS++))
            status="fail"
            ;;
        warn|warning|degraded)
            ((WARNING_CHECKS++))
            status="warn"
            ;;
    esac
    
    RESULTS+=("{\"category\":\"$category\",\"name\":\"$name\",\"status\":\"$status\",\"details\":\"$details\"}")
}

print_check_result() {
    local name="$1"
    local status="$2"
    local details="${3:-}"
    
    if [[ "$OUTPUT_FORMAT" == "minimal" ]]; then
        case "$status" in
            pass) echo "✓ $name" ;;
            fail) echo "✗ $name" ;;
            warn) echo "⚠ $name" ;;
        esac
        return
    fi
    
    local color status_text
    case "$status" in
        pass)
            color=$GREEN
            status_text="✓ Pass"
            ;;
        fail)
            color=$RED
            status_text="✗ Fail"
            ;;
        warn)
            color=$YELLOW
            status_text="⚠ Warn"
            ;;
    esac
    
    printf "  %-30s ${color}%-10s${NC}" "$name" "$status_text"
    
    if [[ -n "$details" ]]; then
        echo -e " ${GRAY}$details${NC}"
    else
        echo ""
    fi
}

# ============================================================================
# ENVIRONMENT CHECKS
# ============================================================================

check_environment() {
    if [[ "$OUTPUT_FORMAT" != "json" ]]; then
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}${BOLD}  Environment Checks${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
    
    # Python
    local python_status="fail"
    local python_details=""
    if command_exists python3; then
        local version
        version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if version_gte "$version" "3.10"; then
            python_status="pass"
            python_details="v$version"
        else
            python_status="warn"
            python_details="v$version (recommend 3.10+)"
        fi
    fi
    record_result "environment" "Python" "$python_status" "$python_details"
    print_check_result "Python" "$python_status" "$python_details"
    
    # Virtual environment
    local venv_status="fail"
    local venv_details=""
    if [[ -d "$VENV_DIR" ]] && [[ -f "$VENV_DIR/bin/activate" ]]; then
        if [[ -f "$VENV_DIR/bin/pip" ]]; then
            venv_status="pass"
            venv_details="$VENV_DIR"
        else
            venv_status="warn"
            venv_details="incomplete"
        fi
    else
        venv_details="not found"
    fi
    record_result "environment" "Virtual Environment" "$venv_status" "$venv_details"
    print_check_result "Virtual Environment" "$venv_status" "$venv_details"
    
    # nexus_lib
    local lib_status="fail"
    local lib_details=""
    if [[ -f "$VENV_DIR/bin/python" ]]; then
        if "$VENV_DIR/bin/python" -c "import nexus_lib" 2>/dev/null; then
            local lib_version
            lib_version=$("$VENV_DIR/bin/python" -c "import nexus_lib; print(nexus_lib.__version__)" 2>/dev/null || echo "unknown")
            lib_status="pass"
            lib_details="v$lib_version"
        else
            lib_details="not installed"
        fi
    else
        lib_details="venv missing"
    fi
    record_result "environment" "nexus_lib" "$lib_status" "$lib_details"
    print_check_result "nexus_lib" "$lib_status" "$lib_details"
    
    # .env file
    local env_status="fail"
    local env_details=""
    if [[ -f "$NEXUS_PROJECT_ROOT/.env" ]]; then
        env_status="pass"
        local key_count
        key_count=$(grep -c "=" "$NEXUS_PROJECT_ROOT/.env" 2>/dev/null || echo "0")
        env_details="$key_count keys"
    else
        env_details="not found"
    fi
    record_result "environment" ".env File" "$env_status" "$env_details"
    print_check_result ".env File" "$env_status" "$env_details"
}

# ============================================================================
# DOCKER CHECKS
# ============================================================================

check_docker() {
    if [[ "$OUTPUT_FORMAT" != "json" ]]; then
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}${BOLD}  Docker Checks${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
    
    # Docker installed
    local docker_status="fail"
    local docker_details=""
    if docker_installed; then
        docker_status="pass"
        docker_details="v$(docker_version)"
    else
        docker_details="not installed"
    fi
    record_result "docker" "Docker Installed" "$docker_status" "$docker_details"
    print_check_result "Docker Installed" "$docker_status" "$docker_details"
    
    # Docker running
    local running_status="fail"
    local running_details=""
    if docker_running; then
        running_status="pass"
        running_details="daemon active"
    else
        running_details="daemon not running"
    fi
    record_result "docker" "Docker Running" "$running_status" "$running_details"
    print_check_result "Docker Running" "$running_status" "$running_details"
    
    # Docker Compose
    local compose_status="fail"
    local compose_details=""
    if compose_available; then
        compose_status="pass"
        compose_details="v$(compose_version)"
    else
        compose_details="not available"
    fi
    record_result "docker" "Docker Compose" "$compose_status" "$compose_details"
    print_check_result "Docker Compose" "$compose_status" "$compose_details"
    
    # Containers
    if docker_running; then
        local container_count
        container_count=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
        local container_status="warn"
        local container_details="$container_count running"
        
        if [[ "$container_count" -gt 0 ]]; then
            container_status="pass"
        else
            container_details="none running"
        fi
        
        record_result "docker" "Containers" "$container_status" "$container_details"
        print_check_result "Containers" "$container_status" "$container_details"
    fi
}

# ============================================================================
# SERVICE HEALTH CHECKS
# ============================================================================

check_services() {
    if [[ "$OUTPUT_FORMAT" != "json" ]]; then
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}${BOLD}  Service Health Checks${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
    
    # Define services
    local services=(
        "Orchestrator:http://localhost:8080/health"
        "Jira Agent:http://localhost:8081/health"
        "Git/CI Agent:http://localhost:8082/health"
        "Reporting Agent:http://localhost:8083/health"
        "Slack Agent:http://localhost:8084/health"
        "Hygiene Agent:http://localhost:8085/health"
        "RCA Agent:http://localhost:8006/health"
        "Analytics:http://localhost:8086/health"
        "Webhooks:http://localhost:8087/health"
        "Admin Dashboard:http://localhost:8088/health"
    )
    
    # Check in parallel
    local temp_dir
    temp_dir=$(mktemp -d)
    local pids=()
    
    for i in "${!services[@]}"; do
        local entry="${services[$i]}"
        local name="${entry%%:*}"
        local url="${entry#*:}"
        
        (
            local start_time end_time latency code
            start_time=$(date +%s%3N)
            code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$CHECK_TIMEOUT" "$url" 2>/dev/null || echo "000")
            end_time=$(date +%s%3N)
            latency=$((end_time - start_time))
            
            echo "$name|$code|$latency" > "$temp_dir/result_$i"
        ) &
        pids+=($!)
    done
    
    # Wait for all checks
    for pid in "${pids[@]}"; do
        wait "$pid" 2>/dev/null || true
    done
    
    # Collect results
    for file in "$temp_dir"/result_*; do
        [[ -f "$file" ]] || continue
        
        local content name code latency
        content=$(cat "$file")
        name="${content%%|*}"
        content="${content#*|}"
        code="${content%%|*}"
        latency="${content#*|}"
        
        local status details
        if [[ "$code" == "200" ]]; then
            status="pass"
            details="${latency}ms"
        elif [[ "$code" == "000" ]]; then
            status="fail"
            details="offline"
        else
            status="warn"
            details="HTTP $code"
        fi
        
        record_result "services" "$name" "$status" "$details"
        print_check_result "$name" "$status" "$details"
    done
    
    rm -rf "$temp_dir"
}

# ============================================================================
# OBSERVABILITY CHECKS
# ============================================================================

check_observability() {
    if [[ "$OUTPUT_FORMAT" != "json" ]]; then
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}${BOLD}  Observability Stack${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
    
    local services=(
        "Prometheus:http://localhost:9090/-/healthy"
        "Grafana:http://localhost:3000/api/health"
        "Jaeger:http://localhost:16686/"
    )
    
    for entry in "${services[@]}"; do
        local name="${entry%%:*}"
        local url="${entry#*:}"
        
        local code status details
        code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$CHECK_TIMEOUT" "$url" 2>/dev/null || echo "000")
        
        if [[ "$code" == "200" ]]; then
            status="pass"
            details="healthy"
        elif [[ "$code" == "000" ]]; then
            status="warn"
            details="offline"
        else
            status="warn"
            details="HTTP $code"
        fi
        
        record_result "observability" "$name" "$status" "$details"
        print_check_result "$name" "$status" "$details"
    done
}

# ============================================================================
# NETWORK CHECKS
# ============================================================================

check_network() {
    if [[ "$OUTPUT_FORMAT" != "json" ]]; then
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}${BOLD}  Network Connectivity${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    fi
    
    # Internet
    local internet_status="fail"
    local internet_details=""
    if has_internet; then
        internet_status="pass"
        internet_details="connected"
    else
        internet_details="no connection"
    fi
    record_result "network" "Internet" "$internet_status" "$internet_details"
    print_check_result "Internet" "$internet_status" "$internet_details"
    
    # DNS
    local dns_status="fail"
    local dns_details=""
    if command_exists host; then
        if host github.com &>/dev/null; then
            dns_status="pass"
            dns_details="resolving"
        else
            dns_details="not resolving"
        fi
    elif command_exists nslookup; then
        if nslookup github.com &>/dev/null; then
            dns_status="pass"
            dns_details="resolving"
        else
            dns_details="not resolving"
        fi
    else
        dns_status="warn"
        dns_details="no dns tool"
    fi
    record_result "network" "DNS" "$dns_status" "$dns_details"
    print_check_result "DNS" "$dns_status" "$dns_details"
    
    # PyPI
    local pypi_status="warn"
    local pypi_details=""
    if check_url "https://pypi.org/simple/" "200" 3 > /dev/null 2>&1; then
        pypi_status="pass"
        pypi_details="reachable"
    else
        pypi_details="unreachable"
    fi
    record_result "network" "PyPI" "$pypi_status" "$pypi_details"
    print_check_result "PyPI" "$pypi_status" "$pypi_details"
    
    # Docker Hub
    local dockerhub_status="warn"
    local dockerhub_details=""
    if check_url "https://registry.hub.docker.com/v2/" "401" 3 > /dev/null 2>&1; then
        dockerhub_status="pass"
        dockerhub_details="reachable"
    else
        dockerhub_details="unreachable"
    fi
    record_result "network" "Docker Hub" "$dockerhub_status" "$dockerhub_details"
    print_check_result "Docker Hub" "$dockerhub_status" "$dockerhub_details"
}

# ============================================================================
# SUMMARY
# ============================================================================

print_summary() {
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        # Output JSON
        echo "{"
        echo "  \"total\": $TOTAL_CHECKS,"
        echo "  \"passed\": $PASSED_CHECKS,"
        echo "  \"failed\": $FAILED_CHECKS,"
        echo "  \"warnings\": $WARNING_CHECKS,"
        echo "  \"results\": ["
        local first=true
        for result in "${RESULTS[@]}"; do
            if $first; then
                first=false
            else
                echo ","
            fi
            echo -n "    $result"
        done
        echo ""
        echo "  ]"
        echo "}"
        return
    fi
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}${BOLD}  Summary${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    local pass_rate=0
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        pass_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    fi
    
    echo -e "  Total Checks:  ${WHITE}$TOTAL_CHECKS${NC}"
    echo -e "  Passed:        ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "  Failed:        ${RED}$FAILED_CHECKS${NC}"
    echo -e "  Warnings:      ${YELLOW}$WARNING_CHECKS${NC}"
    echo ""
    
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        if [[ $WARNING_CHECKS -eq 0 ]]; then
            echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║   ✅ ALL CHECKS PASSED! ($pass_rate%)                                 ║${NC}"
            echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
        else
            echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${YELLOW}║   ⚠️  MOSTLY OK with warnings ($pass_rate%)                          ║${NC}"
            echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════════════╝${NC}"
        fi
    else
        echo -e "${RED}╔═══════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║   ❌ SOME CHECKS FAILED ($pass_rate%)                                  ║${NC}"
        echo -e "${RED}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    fi
    echo ""
}

# ============================================================================
# HELP
# ============================================================================

show_help() {
    print_help_header "nexus verify.sh" "$NEXUS_SCRIPT_VERSION" "System Verification Script"
    
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./scripts/verify.sh [OPTIONS]"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --format FORMAT   Output format: table, json, minimal (default: table)"
    echo "  --timeout SECS    Health check timeout in seconds (default: 5)"
    echo "  --services        Check services only"
    echo "  --docker          Check Docker only"
    echo "  --network         Check network only"
    echo "  --env             Check environment only"
    echo "  --all             Run all checks (default)"
    echo "  --help, -h        Show this help"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./scripts/verify.sh                    # All checks, table format"
    echo "  ./scripts/verify.sh --format json      # JSON output"
    echo "  ./scripts/verify.sh --services         # Services only"
    echo "  ./scripts/verify.sh --timeout 10       # 10s timeout for checks"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    local check_services=false
    local check_docker=false
    local check_network=false
    local check_env=false
    local check_all=true
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --timeout)
                CHECK_TIMEOUT="$2"
                shift 2
                ;;
            --services)
                check_services=true
                check_all=false
                shift
                ;;
            --docker)
                check_docker=true
                check_all=false
                shift
                ;;
            --network)
                check_network=true
                check_all=false
                shift
                ;;
            --env)
                check_env=true
                check_all=false
                shift
                ;;
            --all)
                check_all=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Print banner (unless JSON)
    if [[ "$OUTPUT_FORMAT" != "json" ]]; then
        echo ""
        echo -e "${CYAN}${BOLD}🔍 Nexus System Verification${NC}"
        echo -e "${GRAY}Running comprehensive health checks...${NC}"
    fi
    
    # Run checks
    if $check_all; then
        check_environment
        check_docker
        check_services
        check_observability
        check_network
    else
        $check_env && check_environment
        $check_docker && check_docker
        $check_services && { check_services; check_observability; }
        $check_network && check_network
    fi
    
    # Print summary
    print_summary
    
    # Exit with appropriate code
    if [[ $FAILED_CHECKS -gt 0 ]]; then
        exit 1
    fi
    exit 0
}

# Run main
main "$@"
