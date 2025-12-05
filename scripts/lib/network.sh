#!/usr/bin/env bash
# ============================================================================
# NEXUS RELEASE AUTOMATION - NETWORK UTILITIES LIBRARY
# ============================================================================
# Version: 3.0.0
# Description: Network connectivity and URL utilities
# ============================================================================
#
# REQUIRES: common.sh must be sourced first
#
# PROVIDES:
#   - URL health checking (check_url, wait_for_url)
#   - Network connectivity tests (has_internet, test_connectivity)
#   - Port checking (is_port_open, wait_for_port)
#   - Parallel health checks (check_services)
#
# ============================================================================

# Ensure common.sh is loaded
if [[ -z "${__NEXUS_COMMON_LOADED:-}" ]]; then
    echo "ERROR: common.sh must be sourced before network.sh" >&2
    exit 1
fi

# Prevent multiple sourcing
[[ -n "${__NEXUS_NETWORK_LOADED:-}" ]] && return
readonly __NEXUS_NETWORK_LOADED=1

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default timeouts
NEXUS_HTTP_TIMEOUT="${NEXUS_HTTP_TIMEOUT:-10}"
NEXUS_CONNECT_TIMEOUT="${NEXUS_CONNECT_TIMEOUT:-5}"

# Test URLs for internet connectivity
NEXUS_CONNECTIVITY_URLS=(
    "https://httpbin.org/status/200"
    "https://www.google.com"
    "https://github.com"
)

# ============================================================================
# URL HEALTH CHECKING
# ============================================================================

# Check if a URL is reachable and returns expected status
# Usage: check_url "http://localhost:8080/health" [expected_code] [timeout]
# Returns: 0 if success, 1 otherwise
# Output: JSON with status, code, latency
check_url() {
    local url="$1"
    local expected="${2:-200}"
    local timeout="${3:-$NEXUS_HTTP_TIMEOUT}"
    
    local start_time
    local end_time
    local response_code
    local latency
    
    start_time=$(date +%s%3N)
    
    response_code=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time "$timeout" \
        --connect-timeout "$NEXUS_CONNECT_TIMEOUT" \
        "$url" 2>/dev/null || echo "000")
    
    end_time=$(date +%s%3N)
    latency=$((end_time - start_time))
    
    local status="unknown"
    if [[ "$response_code" == "$expected" ]]; then
        status="healthy"
    elif [[ "$response_code" == "000" ]]; then
        status="unreachable"
    else
        status="unhealthy"
    fi
    
    # Output JSON
    echo "{\"url\":\"$url\",\"status\":\"$status\",\"code\":\"$response_code\",\"latency_ms\":$latency}"
    
    [[ "$status" == "healthy" ]]
}

# Wait for a URL to become available
# Usage: wait_for_url "http://localhost:8080/health" [max_wait] [interval]
# Returns: 0 if available, 1 if timeout
wait_for_url() {
    local url="$1"
    local max_wait="${2:-60}"
    local interval="${3:-2}"
    local elapsed=0
    
    log DEBUG "Waiting for URL: $url (max ${max_wait}s)"
    
    while [[ $elapsed -lt $max_wait ]]; do
        if check_url "$url" "200" 3 > /dev/null 2>&1; then
            log DEBUG "URL available after ${elapsed}s: $url"
            return 0
        fi
        
        sleep "$interval"
        elapsed=$((elapsed + interval))
        
        # Update progress
        progress_bar $elapsed $max_wait "Waiting for $url"
    done
    
    echo ""
    log WARNING "Timeout waiting for URL: $url"
    return 1
}

# ============================================================================
# PORT CHECKING
# ============================================================================

# Check if a port is open
# Usage: is_port_open "localhost" 8080 [timeout]
is_port_open() {
    local host="$1"
    local port="$2"
    local timeout="${3:-2}"
    
    if command_exists nc; then
        nc -z -w"$timeout" "$host" "$port" 2>/dev/null
    elif command_exists bash; then
        timeout "$timeout" bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null
    else
        # Fallback to curl
        curl -s --connect-timeout "$timeout" "http://$host:$port" &>/dev/null
        # Port is open if curl connects (even with error response)
        [[ $? -ne 7 ]]
    fi
}

# Wait for a port to become available
# Usage: wait_for_port "localhost" 8080 [max_wait] [interval]
wait_for_port() {
    local host="$1"
    local port="$2"
    local max_wait="${3:-30}"
    local interval="${4:-1}"
    local elapsed=0
    
    while [[ $elapsed -lt $max_wait ]]; do
        if is_port_open "$host" "$port" 1; then
            return 0
        fi
        
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    
    return 1
}

# ============================================================================
# INTERNET CONNECTIVITY
# ============================================================================

# Check if internet is available
# Usage: has_internet && echo "Online"
has_internet() {
    local url
    
    for url in "${NEXUS_CONNECTIVITY_URLS[@]}"; do
        if check_url "$url" "200" 3 > /dev/null 2>&1; then
            return 0
        fi
    done
    
    return 1
}

# Test network connectivity with details
# Usage: test_connectivity
test_connectivity() {
    local results=()
    
    log SUBSTEP "Testing network connectivity..."
    
    # DNS resolution
    if command_exists host; then
        if host github.com &>/dev/null; then
            results+=("DNS: ✓")
        else
            results+=("DNS: ✗")
        fi
    fi
    
    # Internet access
    if has_internet; then
        results+=("Internet: ✓")
    else
        results+=("Internet: ✗")
    fi
    
    # Docker registry
    if check_url "https://registry.hub.docker.com/v2/" "401" 5 > /dev/null 2>&1; then
        results+=("Docker Hub: ✓")
    else
        results+=("Docker Hub: ✗")
    fi
    
    # npm registry
    if check_url "https://registry.npmjs.org/" "200" 5 > /dev/null 2>&1; then
        results+=("npm Registry: ✓")
    else
        results+=("npm Registry: ✗")
    fi
    
    # PyPI
    if check_url "https://pypi.org/simple/" "200" 5 > /dev/null 2>&1; then
        results+=("PyPI: ✓")
    else
        results+=("PyPI: ✗")
    fi
    
    # Print results
    for result in "${results[@]}"; do
        if [[ "$result" == *"✓"* ]]; then
            echo -e "    ${GREEN}$result${NC}"
        else
            echo -e "    ${RED}$result${NC}"
        fi
    done
    
    # Return success if internet is available
    has_internet
}

# ============================================================================
# SERVICE HEALTH CHECKING
# ============================================================================

# Service definition type
# Format: "name:url:expected_code"
declare -a NEXUS_SERVICES=()

# Register a service for health checking
# Usage: register_service "name" "url" [expected_code]
register_service() {
    local name="$1"
    local url="$2"
    local expected="${3:-200}"
    
    NEXUS_SERVICES+=("${name}:${url}:${expected}")
}

# Check all registered services
# Usage: check_services
# Output: Table with service status
check_services() {
    local total=0
    local healthy=0
    local unhealthy=0
    local results=()
    
    if [[ ${#NEXUS_SERVICES[@]} -eq 0 ]]; then
        log WARNING "No services registered"
        return 0
    fi
    
    echo ""
    echo -e "  ${WHITE}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "  ${WHITE}│${NC}  ${BOLD}Service Health Check${NC}                                       ${WHITE}│${NC}"
    echo -e "  ${WHITE}├─────────────────────────────────────────────────────────────┤${NC}"
    
    for service in "${NEXUS_SERVICES[@]}"; do
        IFS=':' read -r name url expected <<< "$service"
        ((total++))
        
        local result
        result=$(check_url "$url" "$expected" 5)
        local status
        status=$(echo "$result" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        local code
        code=$(echo "$result" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
        local latency
        latency=$(echo "$result" | grep -o '"latency_ms":[0-9]*' | cut -d':' -f2)
        
        local color status_text
        case "$status" in
            healthy)
                color=$GREEN
                status_text="✓ Healthy"
                ((healthy++))
                ;;
            unreachable)
                color=$RED
                status_text="✗ Offline"
                ((unhealthy++))
                ;;
            *)
                color=$YELLOW
                status_text="⚠ HTTP $code"
                ((unhealthy++))
                ;;
        esac
        
        printf "  ${WHITE}│${NC}  %-20s ${color}%-12s${NC} ${GRAY}%4dms${NC}        ${WHITE}│${NC}\n" \
            "$name" "$status_text" "$latency"
    done
    
    echo -e "  ${WHITE}├─────────────────────────────────────────────────────────────┤${NC}"
    printf "  ${WHITE}│${NC}  Total: ${WHITE}%d${NC}  │  ${GREEN}Healthy: %d${NC}  │  ${RED}Unhealthy: %d${NC}           ${WHITE}│${NC}\n" \
        "$total" "$healthy" "$unhealthy"
    echo -e "  ${WHITE}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    
    [[ $unhealthy -eq 0 ]]
}

# Check services in parallel (faster for many services)
# Usage: check_services_parallel [timeout]
check_services_parallel() {
    local timeout="${1:-5}"
    local temp_dir
    temp_dir=$(mktemp -d)
    local pids=()
    
    if [[ ${#NEXUS_SERVICES[@]} -eq 0 ]]; then
        log WARNING "No services registered"
        rm -rf "$temp_dir"
        return 0
    fi
    
    # Start all checks in parallel
    for i in "${!NEXUS_SERVICES[@]}"; do
        local service="${NEXUS_SERVICES[$i]}"
        IFS=':' read -r name url expected <<< "$service"
        
        (
            local result
            result=$(check_url "$url" "$expected" "$timeout")
            echo "$name|$result" > "$temp_dir/result_$i"
        ) &
        pids+=($!)
    done
    
    # Wait for all checks to complete
    for pid in "${pids[@]}"; do
        wait "$pid" 2>/dev/null || true
    done
    
    # Collect and display results
    local total=0
    local healthy=0
    
    echo ""
    echo -e "  ${WHITE}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "  ${WHITE}│${NC}  ${BOLD}Service Health Check (Parallel)${NC}                            ${WHITE}│${NC}"
    echo -e "  ${WHITE}├─────────────────────────────────────────────────────────────┤${NC}"
    
    for file in "$temp_dir"/result_*; do
        [[ -f "$file" ]] || continue
        ((total++))
        
        local content
        content=$(cat "$file")
        local name="${content%%|*}"
        local result="${content#*|}"
        
        local status
        status=$(echo "$result" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        local latency
        latency=$(echo "$result" | grep -o '"latency_ms":[0-9]*' | cut -d':' -f2)
        
        local color status_text
        if [[ "$status" == "healthy" ]]; then
            color=$GREEN
            status_text="✓ Healthy"
            ((healthy++))
        else
            color=$RED
            status_text="✗ Offline"
        fi
        
        printf "  ${WHITE}│${NC}  %-20s ${color}%-12s${NC} ${GRAY}%4dms${NC}        ${WHITE}│${NC}\n" \
            "$name" "$status_text" "${latency:-0}"
    done
    
    echo -e "  ${WHITE}└─────────────────────────────────────────────────────────────┘${NC}"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    [[ $healthy -eq $total ]]
}

# ============================================================================
# COMMON SERVICE REGISTRATIONS
# ============================================================================

# Register all standard Nexus services
# Usage: register_nexus_services
register_nexus_services() {
    NEXUS_SERVICES=()
    
    register_service "Orchestrator" "http://localhost:8080/health"
    register_service "Jira Agent" "http://localhost:8081/health"
    register_service "Git/CI Agent" "http://localhost:8082/health"
    register_service "Reporting Agent" "http://localhost:8083/health"
    register_service "Slack Agent" "http://localhost:8084/health"
    register_service "Hygiene Agent" "http://localhost:8085/health"
    register_service "RCA Agent" "http://localhost:8006/health"
    register_service "Analytics" "http://localhost:8086/health"
    register_service "Webhooks" "http://localhost:8087/health"
    register_service "Admin Dashboard" "http://localhost:8088/health"
}

# Register observability services
# Usage: register_observability_services
register_observability_services() {
    register_service "Prometheus" "http://localhost:9090/-/healthy"
    register_service "Grafana" "http://localhost:3000/api/health"
    register_service "Jaeger" "http://localhost:16686/"
}

# Register infrastructure services
# Usage: register_infrastructure_services
register_infrastructure_services() {
    register_service "Redis" "http://localhost:6379"
    register_service "PostgreSQL" "http://localhost:5432"
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f check_url wait_for_url
export -f is_port_open wait_for_port
export -f has_internet test_connectivity
export -f register_service check_services check_services_parallel
export -f register_nexus_services register_observability_services register_infrastructure_services

log DEBUG "Nexus network library loaded"

