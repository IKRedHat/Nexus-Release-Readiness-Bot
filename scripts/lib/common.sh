#!/usr/bin/env bash
# ============================================================================
# NEXUS RELEASE AUTOMATION - SHARED BASH LIBRARY
# ============================================================================
# Version: 3.0.0
# Description: Core utilities for all Nexus scripts
# ============================================================================
#
# USAGE:
#   source "$(dirname "${BASH_SOURCE[0]}")/lib/common.sh"
#
# PROVIDES:
#   - Logging (log INFO/SUCCESS/WARNING/ERROR/DEBUG/STEP)
#   - Progress indicators (spinner, progress_bar)
#   - Command execution with retry (run_with_retry, run_live)
#   - State management (save_state, get_state, clear_state)
#   - Lock file management (acquire_lock, release_lock)
#   - Network utilities (check_url, wait_for_url)
#   - Version comparison (version_gte)
#   - User prompts (confirm, prompt)
#   - Cleanup handlers (register_cleanup)
#
# ============================================================================

# Prevent multiple sourcing
[[ -n "${__NEXUS_COMMON_LOADED:-}" ]] && return
readonly __NEXUS_COMMON_LOADED=1

# ============================================================================
# STRICT MODE & ERROR HANDLING
# ============================================================================

# Exit on undefined variables
set -u

# Store original options for restoration
__NEXUS_ORIGINAL_OPTS=$(set +o)

# ============================================================================
# COLOR & FORMATTING DEFINITIONS
# ============================================================================

# Check if terminal supports colors
if [[ -t 1 ]] && command -v tput &>/dev/null && [[ $(tput colors 2>/dev/null || echo 0) -ge 8 ]]; then
    readonly NEXUS_COLOR_SUPPORT=true
    
    # Standard colors
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly PURPLE='\033[0;35m'
    readonly CYAN='\033[0;36m'
    readonly WHITE='\033[1;37m'
    readonly GRAY='\033[0;90m'
    readonly NC='\033[0m'  # No Color
    
    # Formatting
    readonly BOLD='\033[1m'
    readonly DIM='\033[2m'
    readonly ITALIC='\033[3m'
    readonly UNDERLINE='\033[4m'
    readonly BLINK='\033[5m'
    readonly REVERSE='\033[7m'
    readonly RESET='\033[0m'
    
    # Background colors
    readonly BG_RED='\033[41m'
    readonly BG_GREEN='\033[42m'
    readonly BG_YELLOW='\033[43m'
    readonly BG_BLUE='\033[44m'
else
    readonly NEXUS_COLOR_SUPPORT=false
    readonly RED='' GREEN='' YELLOW='' BLUE='' PURPLE='' CYAN='' WHITE='' GRAY='' NC=''
    readonly BOLD='' DIM='' ITALIC='' UNDERLINE='' BLINK='' REVERSE='' RESET=''
    readonly BG_RED='' BG_GREEN='' BG_YELLOW='' BG_BLUE=''
fi

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================

# Script identification (to be set by sourcing script)
NEXUS_SCRIPT_NAME="${NEXUS_SCRIPT_NAME:-nexus}"
NEXUS_SCRIPT_VERSION="${NEXUS_SCRIPT_VERSION:-3.0.0}"

# Directories
NEXUS_PROJECT_ROOT="${NEXUS_PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
NEXUS_STATE_DIR="${NEXUS_STATE_DIR:-$NEXUS_PROJECT_ROOT/.nexus}"
NEXUS_LOG_DIR="${NEXUS_LOG_DIR:-$NEXUS_PROJECT_ROOT/logs}"
NEXUS_BACKUP_DIR="${NEXUS_BACKUP_DIR:-$NEXUS_PROJECT_ROOT/.nexus/backups}"

# Files
NEXUS_LOG_FILE="${NEXUS_LOG_FILE:-$NEXUS_LOG_DIR/${NEXUS_SCRIPT_NAME}.log}"
NEXUS_STATE_FILE="${NEXUS_STATE_FILE:-$NEXUS_STATE_DIR/${NEXUS_SCRIPT_NAME}.state}"
NEXUS_LOCK_FILE="${NEXUS_LOCK_FILE:-$NEXUS_STATE_DIR/${NEXUS_SCRIPT_NAME}.lock}"

# Retry configuration
NEXUS_MAX_RETRIES="${NEXUS_MAX_RETRIES:-3}"
NEXUS_RETRY_DELAY="${NEXUS_RETRY_DELAY:-5}"
NEXUS_TIMEOUT="${NEXUS_TIMEOUT:-300}"

# Feature flags
NEXUS_VERBOSE="${NEXUS_VERBOSE:-false}"
NEXUS_DEBUG="${NEXUS_DEBUG:-false}"
NEXUS_DRY_RUN="${NEXUS_DRY_RUN:-false}"
NEXUS_NON_INTERACTIVE="${NEXUS_NON_INTERACTIVE:-false}"
NEXUS_NO_COLOR="${NEXUS_NO_COLOR:-false}"

# Ensure directories exist
mkdir -p "$NEXUS_STATE_DIR" "$NEXUS_LOG_DIR" "$NEXUS_BACKUP_DIR" 2>/dev/null || true

# ============================================================================
# CLEANUP HANDLERS
# ============================================================================

# Array to store cleanup functions
declare -a __NEXUS_CLEANUP_HANDLERS=()

# Register a cleanup function
# Usage: register_cleanup "function_name"
register_cleanup() {
    __NEXUS_CLEANUP_HANDLERS+=("$1")
}

# Execute all registered cleanup handlers
__nexus_run_cleanup() {
    local exit_code=$?
    
    # Run handlers in reverse order
    local i
    for ((i=${#__NEXUS_CLEANUP_HANDLERS[@]}-1; i>=0; i--)); do
        local handler="${__NEXUS_CLEANUP_HANDLERS[$i]}"
        if declare -F "$handler" &>/dev/null; then
            "$handler" "$exit_code" || true
        fi
    done
    
    # Restore original options
    eval "$__NEXUS_ORIGINAL_OPTS"
}

# Set up trap for cleanup
trap __nexus_run_cleanup EXIT

# ============================================================================
# LOGGING SYSTEM
# ============================================================================

# Internal: Format timestamp
__nexus_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Internal: Write to log file
__nexus_log_to_file() {
    local level="$1"
    shift
    echo "[$(__nexus_timestamp)] [$level] $*" >> "$NEXUS_LOG_FILE" 2>/dev/null || true
}

# Main logging function
# Usage: log LEVEL "message"
# Levels: INFO, SUCCESS, WARNING, ERROR, DEBUG, STEP, SUBSTEP, PROGRESS
log() {
    local level="${1:-INFO}"
    shift
    local message="$*"
    
    # Always log to file
    __nexus_log_to_file "$level" "$message"
    
    # Check if we should display
    if [[ "$level" == "DEBUG" && "$NEXUS_DEBUG" != "true" ]]; then
        return 0
    fi
    
    # Format output based on level
    case "$level" in
        INFO)
            echo -e "  ${BLUE}ℹ${NC}  $message"
            ;;
        SUCCESS)
            echo -e "  ${GREEN}✓${NC}  ${GREEN}$message${NC}"
            ;;
        WARNING)
            echo -e "  ${YELLOW}⚠${NC}  ${YELLOW}$message${NC}"
            ;;
        ERROR)
            echo -e "  ${RED}✗${NC}  ${RED}$message${NC}" >&2
            ;;
        DEBUG)
            echo -e "  ${GRAY}⋯${NC}  ${GRAY}$message${NC}"
            ;;
        STEP)
            echo ""
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${CYAN}${BOLD}  ▶ $message${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            ;;
        SUBSTEP)
            echo -e "  ${WHITE}→${NC} $message"
            ;;
        PROGRESS)
            echo -ne "\r  ${CYAN}⟳${NC}  $message"
            ;;
        PROGRESS_DONE)
            echo -e "\r  ${GREEN}✓${NC}  $message                    "
            ;;
        DRY_RUN)
            echo -e "  ${GRAY}[DRY-RUN]${NC} Would: $message"
            ;;
        *)
            echo -e "  $message"
            ;;
    esac
}

# ============================================================================
# PROGRESS INDICATORS
# ============================================================================

# Display a spinner while a process runs
# Usage: spinner PID "message"
spinner() {
    local pid=$1
    local message="${2:-Processing}"
    local spin_chars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r  ${CYAN}%s${NC} %s" "${spin_chars:i++%10:1}" "$message"
        sleep 0.1
    done
    
    wait "$pid"
    return $?
}

# Display a progress bar
# Usage: progress_bar CURRENT TOTAL "message"
progress_bar() {
    local current=$1
    local total=$2
    local message="${3:-Progress}"
    local width=${4:-40}
    
    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    printf "\r  ${CYAN}⟳${NC}  %s [" "$message"
    printf "%${filled}s" | tr ' ' '█'
    printf "%${empty}s" | tr ' ' '░'
    printf "] %3d%%" "$percent"
    
    if [[ $current -eq $total ]]; then
        echo ""
    fi
}

# ============================================================================
# COMMAND EXECUTION WITH RETRY
# ============================================================================

# Run a command with automatic retry on failure
# Usage: run_with_retry "description" command [args...]
# Returns: 0 on success, 1 on failure after all retries
run_with_retry() {
    local description="$1"
    shift
    local attempt=1
    local status=0
    
    while [[ $attempt -le $NEXUS_MAX_RETRIES ]]; do
        log DEBUG "Attempt $attempt/$NEXUS_MAX_RETRIES: $*"
        
        # Show attempt indicator
        if [[ $attempt -eq 1 ]]; then
            echo -ne "  ${WHITE}→${NC} $description... "
        else
            echo -ne "  ${YELLOW}↻${NC} Retry $attempt/$NEXUS_MAX_RETRIES: $description... "
        fi
        
        # Execute command
        if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
            echo -e "${GRAY}[DRY-RUN]${NC}"
            return 0
        fi
        
        if timeout "$NEXUS_TIMEOUT" "$@" >> "$NEXUS_LOG_FILE" 2>&1; then
            echo -e "${GREEN}✓${NC}"
            return 0
        else
            status=$?
            echo -e "${RED}✗${NC}"
            
            if [[ $attempt -lt $NEXUS_MAX_RETRIES ]]; then
                log WARNING "Failed (exit: $status). Retrying in ${NEXUS_RETRY_DELAY}s..."
                sleep "$NEXUS_RETRY_DELAY"
            fi
        fi
        
        attempt=$((attempt + 1))
    done
    
    log ERROR "Failed after $NEXUS_MAX_RETRIES attempts: $description"
    return 1
}

# Run command with live output
# Usage: run_live "description" command [args...]
run_live() {
    local description="$1"
    shift
    
    echo -e "  ${WHITE}→${NC} $description"
    
    if [[ "$NEXUS_DRY_RUN" == "true" ]]; then
        log DRY_RUN "$*"
        return 0
    fi
    
    if [[ "$NEXUS_VERBOSE" == "true" ]]; then
        # Show output in real-time
        if "$@" 2>&1 | tee -a "$NEXUS_LOG_FILE"; then
            log SUCCESS "Completed: $description"
            return 0
        else
            log ERROR "Failed: $description"
            return 1
        fi
    else
        # Show spinner
        "$@" >> "$NEXUS_LOG_FILE" 2>&1 &
        local pid=$!
        
        if spinner $pid "$description"; then
            printf "\r  ${GREEN}✓${NC} %s                              \n" "$description"
            return 0
        else
            printf "\r  ${RED}✗${NC} %s                              \n" "$description"
            return 1
        fi
    fi
}

# Run command silently, only log to file
# Usage: run_silent command [args...]
run_silent() {
    "$@" >> "$NEXUS_LOG_FILE" 2>&1
}

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

# Save state/checkpoint
# Usage: save_state KEY VALUE
save_state() {
    local key="$1"
    local value="${2:-$(date +%s)}"
    
    # Create state file if needed
    touch "$NEXUS_STATE_FILE" 2>/dev/null || true
    
    # Remove existing key
    if [[ -f "$NEXUS_STATE_FILE" ]]; then
        grep -v "^${key}=" "$NEXUS_STATE_FILE" > "${NEXUS_STATE_FILE}.tmp" 2>/dev/null || true
        mv "${NEXUS_STATE_FILE}.tmp" "$NEXUS_STATE_FILE" 2>/dev/null || true
    fi
    
    # Add new key-value
    echo "${key}=${value}" >> "$NEXUS_STATE_FILE"
    log DEBUG "State saved: $key=$value"
}

# Get state value
# Usage: get_state KEY [default]
get_state() {
    local key="$1"
    local default="${2:-}"
    
    if [[ -f "$NEXUS_STATE_FILE" ]]; then
        local value
        value=$(grep "^${key}=" "$NEXUS_STATE_FILE" 2>/dev/null | cut -d'=' -f2-)
        echo "${value:-$default}"
    else
        echo "$default"
    fi
}

# Check if state exists
# Usage: has_state KEY
has_state() {
    local key="$1"
    [[ -f "$NEXUS_STATE_FILE" ]] && grep -q "^${key}=" "$NEXUS_STATE_FILE" 2>/dev/null
}

# Clear all state
# Usage: clear_state
clear_state() {
    rm -f "$NEXUS_STATE_FILE" 2>/dev/null || true
    log DEBUG "State cleared"
}

# Clear specific state key
# Usage: clear_state_key KEY
clear_state_key() {
    local key="$1"
    if [[ -f "$NEXUS_STATE_FILE" ]]; then
        grep -v "^${key}=" "$NEXUS_STATE_FILE" > "${NEXUS_STATE_FILE}.tmp" 2>/dev/null || true
        mv "${NEXUS_STATE_FILE}.tmp" "$NEXUS_STATE_FILE" 2>/dev/null || true
    fi
}

# ============================================================================
# LOCK FILE MANAGEMENT
# ============================================================================

# Acquire an exclusive lock
# Usage: acquire_lock [lock_file]
acquire_lock() {
    local lock_file="${1:-$NEXUS_LOCK_FILE}"
    
    if [[ -f "$lock_file" ]]; then
        local pid
        pid=$(cat "$lock_file" 2>/dev/null)
        
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            log ERROR "Another process is running (PID: $pid)"
            log INFO "If this is incorrect, remove: $lock_file"
            return 1
        fi
        
        # Stale lock, remove it
        rm -f "$lock_file" 2>/dev/null || true
    fi
    
    echo $$ > "$lock_file"
    log DEBUG "Lock acquired: $lock_file"
    
    # Register cleanup to release lock
    __nexus_release_lock_on_exit() {
        rm -f "$lock_file" 2>/dev/null || true
    }
    register_cleanup __nexus_release_lock_on_exit
    
    return 0
}

# Release lock
# Usage: release_lock [lock_file]
release_lock() {
    local lock_file="${1:-$NEXUS_LOCK_FILE}"
    rm -f "$lock_file" 2>/dev/null || true
    log DEBUG "Lock released: $lock_file"
}

# ============================================================================
# USER INTERACTION
# ============================================================================

# Ask for confirmation
# Usage: confirm "question" [default: n]
confirm() {
    local question="$1"
    local default="${2:-n}"
    
    if [[ "$NEXUS_NON_INTERACTIVE" == "true" ]]; then
        [[ "$default" =~ ^[Yy] ]]
        return $?
    fi
    
    local prompt
    if [[ "$default" =~ ^[Yy] ]]; then
        prompt="[Y/n]"
    else
        prompt="[y/N]"
    fi
    
    echo -ne "  ${YELLOW}?${NC}  $question $prompt "
    read -r response
    
    if [[ -z "$response" ]]; then
        [[ "$default" =~ ^[Yy] ]]
        return $?
    fi
    
    [[ "$response" =~ ^[Yy] ]]
}

# Prompt for input
# Usage: prompt "question" [default]
prompt() {
    local question="$1"
    local default="${2:-}"
    
    if [[ "$NEXUS_NON_INTERACTIVE" == "true" ]]; then
        echo "$default"
        return 0
    fi
    
    local prompt_text="$question"
    if [[ -n "$default" ]]; then
        prompt_text="$question [$default]"
    fi
    
    echo -ne "  ${CYAN}?${NC}  $prompt_text: "
    read -r response
    
    if [[ -z "$response" ]]; then
        echo "$default"
    else
        echo "$response"
    fi
}

# Select from options
# Usage: select_option "prompt" "option1" "option2" ...
select_option() {
    local prompt="$1"
    shift
    local options=("$@")
    
    echo -e "  ${CYAN}?${NC}  $prompt"
    local i=1
    for opt in "${options[@]}"; do
        echo -e "      ${WHITE}[$i]${NC} $opt"
        ((i++))
    done
    
    echo -ne "  Enter choice [1-${#options[@]}]: "
    read -r choice
    
    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#options[@]} )); then
        echo "${options[$((choice-1))]}"
    else
        echo "${options[0]}"
    fi
}

# ============================================================================
# VERSION UTILITIES
# ============================================================================

# Compare versions (semantic versioning)
# Usage: version_gte "1.2.3" "1.2.0"
# Returns: 0 if first >= second, 1 otherwise
version_gte() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Compare versions exactly
# Usage: version_eq "1.2.3" "1.2.3"
version_eq() {
    [[ "$1" == "$2" ]]
}

# ============================================================================
# SYSTEM UTILITIES
# ============================================================================

# Detect operating system
# Usage: os=$(get_os)
get_os() {
    case "$(uname -s)" in
        Darwin*)  echo "macos" ;;
        Linux*)   echo "linux" ;;
        MINGW*|CYGWIN*|MSYS*) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

# Detect architecture
# Usage: arch=$(get_arch)
get_arch() {
    case "$(uname -m)" in
        x86_64|amd64) echo "amd64" ;;
        aarch64|arm64) echo "arm64" ;;
        armv7*) echo "armv7" ;;
        *)      echo "unknown" ;;
    esac
}

# Check if command exists
# Usage: command_exists docker
command_exists() {
    command -v "$1" &>/dev/null
}

# Check if running as root
# Usage: is_root && echo "Running as root"
is_root() {
    [[ $EUID -eq 0 ]]
}

# Get available disk space in GB
# Usage: space=$(get_disk_space "/path")
get_disk_space() {
    local path="${1:-.}"
    df -BG "$path" 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G'
}

# Get system memory in MB
# Usage: mem=$(get_memory)
get_memory() {
    if [[ "$(get_os)" == "macos" ]]; then
        sysctl -n hw.memsize 2>/dev/null | awk '{print int($0/1024/1024)}'
    else
        grep MemTotal /proc/meminfo 2>/dev/null | awk '{print int($2/1024)}'
    fi
}

# ============================================================================
# ARRAY UTILITIES
# ============================================================================

# Check if array contains element
# Usage: array_contains "element" "${array[@]}"
array_contains() {
    local element="$1"
    shift
    local arr=("$@")
    
    for item in "${arr[@]}"; do
        [[ "$item" == "$element" ]] && return 0
    done
    return 1
}

# Join array elements
# Usage: result=$(array_join "," "${array[@]}")
array_join() {
    local delimiter="$1"
    shift
    local first="$1"
    shift
    printf '%s' "$first" "${@/#/$delimiter}"
}

# ============================================================================
# FILE UTILITIES
# ============================================================================

# Create backup of file/directory
# Usage: create_backup "/path/to/file" [backup_dir]
create_backup() {
    local source="$1"
    local backup_dir="${2:-$NEXUS_BACKUP_DIR}"
    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_name
    backup_name=$(basename "$source")_$timestamp
    
    mkdir -p "$backup_dir"
    
    if [[ -e "$source" ]]; then
        if cp -r "$source" "$backup_dir/$backup_name"; then
            log SUCCESS "Backup created: $backup_dir/$backup_name"
            echo "$backup_dir/$backup_name"
            return 0
        else
            log ERROR "Failed to create backup of $source"
            return 1
        fi
    fi
    
    return 1
}

# Safe file write (write to temp then move)
# Usage: safe_write "content" "/path/to/file"
safe_write() {
    local content="$1"
    local target="$2"
    local temp_file
    temp_file=$(mktemp)
    
    echo "$content" > "$temp_file"
    mv "$temp_file" "$target"
}

# ============================================================================
# BANNER & DISPLAY UTILITIES
# ============================================================================

# Print Nexus ASCII banner
print_nexus_banner() {
    local color="${1:-$PURPLE}"
    echo -e "${color}"
    cat << 'EOF'
    ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
    ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
    ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
    ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
    ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
EOF
    echo -e "${NC}"
}

# Print a divider line
print_divider() {
    local char="${1:-━}"
    local width="${2:-65}"
    local color="${3:-$CYAN}"
    printf "${color}%${width}s${NC}\n" | tr ' ' "$char"
}

# Print a boxed message
print_box() {
    local message="$1"
    local color="${2:-$GREEN}"
    local width=67
    
    echo -e "${color}╔$(printf '═%.0s' $(seq 1 $((width-2))))╗${NC}"
    printf "${color}║${NC} %-$((width-4))s ${color}║${NC}\n" "$message"
    echo -e "${color}╚$(printf '═%.0s' $(seq 1 $((width-2))))╝${NC}"
}

# ============================================================================
# HELP UTILITIES
# ============================================================================

# Print standard help header
print_help_header() {
    local script_name="$1"
    local version="${2:-$NEXUS_SCRIPT_VERSION}"
    local description="${3:-Nexus Script}"
    
    echo ""
    echo -e "${BOLD}$script_name v$version${NC}"
    echo -e "${GRAY}$description${NC}"
    echo ""
}

# Print usage example
print_usage() {
    local script="$1"
    echo -e "${CYAN}Usage:${NC}"
    echo "  $script [OPTIONS]"
    echo ""
}

# ============================================================================
# EXPORT FUNCTIONS FOR SUBSHELLS
# ============================================================================

export -f log spinner progress_bar run_with_retry run_live run_silent
export -f save_state get_state has_state clear_state clear_state_key
export -f acquire_lock release_lock
export -f confirm prompt select_option
export -f version_gte version_eq
export -f get_os get_arch command_exists is_root get_disk_space get_memory
export -f array_contains array_join
export -f create_backup safe_write
export -f print_nexus_banner print_divider print_box print_help_header print_usage

# ============================================================================
# INITIALIZATION COMPLETE
# ============================================================================

log DEBUG "Nexus common library loaded (v$NEXUS_SCRIPT_VERSION)"

