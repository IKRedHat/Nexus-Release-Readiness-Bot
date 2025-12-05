#!/usr/bin/env bash
# ============================================================================
# NEXUS RELEASE AUTOMATION - UI UTILITIES LIBRARY
# ============================================================================
# Version: 3.0.0
# Description: Advanced UI components for beautiful terminal output
# ============================================================================
#
# PROVIDES:
#   - ASCII banners and logos
#   - Progress bars with stages
#   - Status indicators
#   - Tables and boxes
#   - Animated spinners
#   - Color gradients
#
# ============================================================================

# Ensure common.sh is loaded
if [[ -z "${__NEXUS_COMMON_LOADED:-}" ]]; then
    echo "ERROR: common.sh must be sourced before ui.sh" >&2
    exit 1
fi

# Prevent multiple sourcing
[[ -n "${__NEXUS_UI_LOADED:-}" ]] && return
readonly __NEXUS_UI_LOADED=1

# ============================================================================
# EXTENDED COLOR PALETTE
# ============================================================================

# Bright colors
readonly BRIGHT_RED='\033[1;31m'
readonly BRIGHT_GREEN='\033[1;32m'
readonly BRIGHT_YELLOW='\033[1;33m'
readonly BRIGHT_BLUE='\033[1;34m'
readonly BRIGHT_MAGENTA='\033[1;35m'
readonly BRIGHT_CYAN='\033[1;36m'
readonly BRIGHT_WHITE='\033[1;37m'

# 256 color palette for gradients
readonly ORANGE='\033[38;5;208m'
readonly PINK='\033[38;5;205m'
readonly LIME='\033[38;5;118m'
readonly TEAL='\033[38;5;38m'
readonly CORAL='\033[38;5;209m'
readonly GOLD='\033[38;5;220m'
readonly SKY='\033[38;5;117m'
readonly VIOLET='\033[38;5;135m'

# ============================================================================
# EMOJI & SYMBOLS
# ============================================================================

readonly SYM_CHECK="✓"
readonly SYM_CROSS="✗"
readonly SYM_WARN="⚠"
readonly SYM_INFO="ℹ"
readonly SYM_ARROW="→"
readonly SYM_ROCKET="🚀"
readonly SYM_FIRE="🔥"
readonly SYM_STAR="⭐"
readonly SYM_GEAR="⚙"
readonly SYM_PACKAGE="📦"
readonly SYM_CLOUD="☁️"
readonly SYM_LOCK="🔐"
readonly SYM_KEY="🔑"
readonly SYM_GLOBE="🌐"
readonly SYM_LIGHTNING="⚡"
readonly SYM_SPARKLE="✨"
readonly SYM_HEART="❤️"
readonly SYM_TROPHY="🏆"

# Box drawing characters
readonly BOX_TL="╔"
readonly BOX_TR="╗"
readonly BOX_BL="╚"
readonly BOX_BR="╝"
readonly BOX_H="═"
readonly BOX_V="║"
readonly BOX_ML="╠"
readonly BOX_MR="╣"
readonly BOX_TJ="╦"
readonly BOX_BJ="╩"
readonly BOX_CJ="╬"

# Light box
readonly LBOX_TL="┌"
readonly LBOX_TR="┐"
readonly LBOX_BL="└"
readonly LBOX_BR="┘"
readonly LBOX_H="─"
readonly LBOX_V="│"

# Progress bar characters
readonly PROG_FULL="█"
readonly PROG_HALF="▓"
readonly PROG_LIGHT="░"
readonly PROG_EMPTY=" "

# ============================================================================
# ANIMATED SPINNERS
# ============================================================================

# Spinner styles
declare -a SPINNER_DOTS=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
declare -a SPINNER_LINE=('|' '/' '-' '\')
declare -a SPINNER_CIRCLE=('◐' '◓' '◑' '◒')
declare -a SPINNER_ARROW=('←' '↖' '↑' '↗' '→' '↘' '↓' '↙')
declare -a SPINNER_BOUNCE=('⠁' '⠂' '⠄' '⠂')
declare -a SPINNER_PULSE=('█' '▓' '▒' '░' '▒' '▓')

# Current spinner style
SPINNER_STYLE=("${SPINNER_DOTS[@]}")

# Animated spinner with message
# Usage: start_spinner "message"
#        stop_spinner
__SPINNER_PID=""
__SPINNER_MSG=""

start_spinner() {
    __SPINNER_MSG="$1"
    
    (
        local i=0
        while true; do
            printf "\r  ${CYAN}%s${NC} %s" "${SPINNER_STYLE[i]}" "$__SPINNER_MSG"
            i=$(( (i + 1) % ${#SPINNER_STYLE[@]} ))
            sleep 0.1
        done
    ) &
    __SPINNER_PID=$!
}

stop_spinner() {
    local status="${1:-success}"
    local message="${2:-$__SPINNER_MSG}"
    
    if [[ -n "$__SPINNER_PID" ]]; then
        kill "$__SPINNER_PID" 2>/dev/null
        wait "$__SPINNER_PID" 2>/dev/null
        __SPINNER_PID=""
    fi
    
    case "$status" in
        success)
            printf "\r  ${GREEN}${SYM_CHECK}${NC} %s                              \n" "$message"
            ;;
        error)
            printf "\r  ${RED}${SYM_CROSS}${NC} %s                              \n" "$message"
            ;;
        warning)
            printf "\r  ${YELLOW}${SYM_WARN}${NC} %s                              \n" "$message"
            ;;
        *)
            printf "\r  ${CYAN}${SYM_INFO}${NC} %s                              \n" "$message"
            ;;
    esac
}

# ============================================================================
# PROGRESS BAR WITH STAGES
# ============================================================================

# Stage tracking
declare -a STAGES=()
CURRENT_STAGE=0
TOTAL_STAGES=0

# Initialize stages
# Usage: init_stages "Stage 1" "Stage 2" "Stage 3"
init_stages() {
    STAGES=("$@")
    TOTAL_STAGES=${#STAGES[@]}
    CURRENT_STAGE=0
}

# Print stage header
# Usage: print_stage_header
print_stage_header() {
    local width=70
    
    echo ""
    printf "${CYAN}"
    printf "${BOX_TL}"
    printf "%${width}s" | tr ' ' "${BOX_H}"
    printf "${BOX_TR}\n"
    printf "${BOX_V}${NC}"
    printf " ${BRIGHT_WHITE}%-$((width-1))s${CYAN}${BOX_V}\n" "DEPLOYMENT STAGES"
    printf "${BOX_ML}"
    printf "%${width}s" | tr ' ' "${BOX_H}"
    printf "${BOX_MR}\n"
    printf "${NC}"
    
    local i=1
    for stage in "${STAGES[@]}"; do
        local status_icon="${GRAY}○${NC}"
        local stage_color="${GRAY}"
        
        if [[ $i -lt $CURRENT_STAGE ]]; then
            status_icon="${GREEN}${SYM_CHECK}${NC}"
            stage_color="${GREEN}"
        elif [[ $i -eq $CURRENT_STAGE ]]; then
            status_icon="${CYAN}▶${NC}"
            stage_color="${BRIGHT_WHITE}"
        fi
        
        printf "${CYAN}${BOX_V}${NC}"
        printf "  ${status_icon} ${stage_color}%-$((width-5))s${NC}${CYAN}${BOX_V}\n" "Stage $i: $stage"
        ((i++))
    done
    
    printf "${CYAN}"
    printf "${BOX_BL}"
    printf "%${width}s" | tr ' ' "${BOX_H}"
    printf "${BOX_BR}\n"
    printf "${NC}"
    echo ""
}

# Advance to next stage
# Usage: next_stage
next_stage() {
    ((CURRENT_STAGE++))
    
    if [[ $CURRENT_STAGE -le $TOTAL_STAGES ]]; then
        local stage_name="${STAGES[$((CURRENT_STAGE-1))]}"
        
        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "  ${BRIGHT_CYAN}STAGE $CURRENT_STAGE/$TOTAL_STAGES${NC}: ${BRIGHT_WHITE}$stage_name${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        
        # Progress bar
        local progress=$((CURRENT_STAGE * 100 / TOTAL_STAGES))
        local filled=$((CURRENT_STAGE * 50 / TOTAL_STAGES))
        local empty=$((50 - filled))
        
        printf "  ${GRAY}Progress: ${NC}"
        printf "${GREEN}"
        printf "%${filled}s" | tr ' ' "${PROG_FULL}"
        printf "${GRAY}"
        printf "%${empty}s" | tr ' ' "${PROG_LIGHT}"
        printf "${NC}"
        printf " ${BRIGHT_WHITE}%3d%%${NC}\n" "$progress"
        echo ""
    fi
}

# Mark stage complete
# Usage: stage_complete [message]
stage_complete() {
    local message="${1:-Stage completed}"
    echo -e "  ${GREEN}${SYM_CHECK}${NC} ${GREEN}$message${NC}"
}

# Mark stage failed
# Usage: stage_failed [message]
stage_failed() {
    local message="${1:-Stage failed}"
    echo -e "  ${RED}${SYM_CROSS}${NC} ${RED}$message${NC}"
}

# ============================================================================
# ENHANCED PROGRESS BAR
# ============================================================================

# Colorful progress bar with gradient
# Usage: gradient_progress CURRENT TOTAL "message"
gradient_progress() {
    local current=$1
    local total=$2
    local message="${3:-Progress}"
    local width=${4:-50}
    
    local percent=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    
    # Color gradient based on progress
    local color
    if [[ $percent -lt 25 ]]; then
        color=$RED
    elif [[ $percent -lt 50 ]]; then
        color=$ORANGE
    elif [[ $percent -lt 75 ]]; then
        color=$YELLOW
    elif [[ $percent -lt 100 ]]; then
        color=$LIME
    else
        color=$GREEN
    fi
    
    printf "\r  ${CYAN}⟳${NC}  %-20s ${GRAY}[${NC}" "$message"
    printf "${color}%${filled}s${NC}" | tr ' ' '█'
    printf "${GRAY}%${empty}s${NC}" | tr ' ' '░'
    printf "${GRAY}]${NC} ${BRIGHT_WHITE}%3d%%${NC}" "$percent"
    
    if [[ $current -eq $total ]]; then
        echo ""
    fi
}

# ============================================================================
# BANNERS & HEADERS
# ============================================================================

# Print deployment banner
print_deploy_banner() {
    local platform="${1:-Nexus}"
    
    clear 2>/dev/null || true
    echo -e "${BRIGHT_CYAN}"
    cat << 'EOF'
    
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║   ██████╗ ███████╗██████╗ ██╗      ██████╗ ██╗   ██╗                      ║
    ║   ██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗╚██╗ ██╔╝                      ║
    ║   ██║  ██║█████╗  ██████╔╝██║     ██║   ██║ ╚████╔╝                       ║
    ║   ██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║  ╚██╔╝                        ║
    ║   ██████╔╝███████╗██║     ███████╗╚██████╔╝   ██║                         ║
    ║   ╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝                         ║
    ║                                                                           ║
EOF
    echo -e "    ║   ${WHITE}🚀 Nexus One-Click Deployment System v3.0${BRIGHT_CYAN}                          ║"
    echo -e "    ╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Print Vercel banner
print_vercel_banner() {
    echo -e "${BLACK}${BG_WHITE}"
    cat << 'EOF'
    
     ▲ Vercel Deployment
    
EOF
    echo -e "${NC}"
}

# Print Render banner
print_render_banner() {
    echo -e "${WHITE}${BG_BLUE}"
    cat << 'EOF'
    
     ◉ Render Deployment
    
EOF
    echo -e "${NC}"
}

# Print success banner
print_success_banner() {
    local message="${1:-Deployment Successful!}"
    
    echo ""
    echo -e "${GREEN}"
    echo "    ╔═══════════════════════════════════════════════════════════════════╗"
    echo "    ║                                                                   ║"
    printf "    ║   ${BRIGHT_GREEN}🎉 %-60s${GREEN}║\n" "$message"
    echo "    ║                                                                   ║"
    echo "    ╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Print error banner
print_error_banner() {
    local message="${1:-Deployment Failed}"
    
    echo ""
    echo -e "${RED}"
    echo "    ╔═══════════════════════════════════════════════════════════════════╗"
    echo "    ║                                                                   ║"
    printf "    ║   ${BRIGHT_RED}❌ %-60s${RED}║\n" "$message"
    echo "    ║                                                                   ║"
    echo "    ╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ============================================================================
# TABLES
# ============================================================================

# Print a formatted table
# Usage: print_table "Header1,Header2,Header3" "Row1Col1,Row1Col2,Row1Col3" "Row2Col1,Row2Col2,Row2Col3"
print_table() {
    local headers="$1"
    shift
    local rows=("$@")
    
    # Calculate column widths
    IFS=',' read -ra header_arr <<< "$headers"
    local num_cols=${#header_arr[@]}
    declare -a col_widths
    
    for i in "${!header_arr[@]}"; do
        col_widths[$i]=${#header_arr[$i]}
    done
    
    for row in "${rows[@]}"; do
        IFS=',' read -ra row_arr <<< "$row"
        for i in "${!row_arr[@]}"; do
            local len=${#row_arr[$i]}
            if [[ $len -gt ${col_widths[$i]:-0} ]]; then
                col_widths[$i]=$len
            fi
        done
    done
    
    # Print table
    # Top border
    printf "  ${CYAN}${LBOX_TL}"
    for i in "${!col_widths[@]}"; do
        printf "%$((col_widths[$i] + 2))s" | tr ' ' "${LBOX_H}"
        if [[ $i -lt $((num_cols - 1)) ]]; then
            printf "┬"
        fi
    done
    printf "${LBOX_TR}${NC}\n"
    
    # Headers
    printf "  ${CYAN}${LBOX_V}${NC}"
    for i in "${!header_arr[@]}"; do
        printf " ${BRIGHT_WHITE}%-${col_widths[$i]}s${NC} ${CYAN}${LBOX_V}${NC}" "${header_arr[$i]}"
    done
    printf "\n"
    
    # Header separator
    printf "  ${CYAN}├"
    for i in "${!col_widths[@]}"; do
        printf "%$((col_widths[$i] + 2))s" | tr ' ' "${LBOX_H}"
        if [[ $i -lt $((num_cols - 1)) ]]; then
            printf "┼"
        fi
    done
    printf "┤${NC}\n"
    
    # Rows
    for row in "${rows[@]}"; do
        IFS=',' read -ra row_arr <<< "$row"
        printf "  ${CYAN}${LBOX_V}${NC}"
        for i in "${!row_arr[@]}"; do
            printf " %-${col_widths[$i]}s ${CYAN}${LBOX_V}${NC}" "${row_arr[$i]}"
        done
        printf "\n"
    done
    
    # Bottom border
    printf "  ${CYAN}${LBOX_BL}"
    for i in "${!col_widths[@]}"; do
        printf "%$((col_widths[$i] + 2))s" | tr ' ' "${LBOX_H}"
        if [[ $i -lt $((num_cols - 1)) ]]; then
            printf "┴"
        fi
    done
    printf "${LBOX_BR}${NC}\n"
}

# ============================================================================
# KEY-VALUE DISPLAY
# ============================================================================

# Print key-value pairs nicely
# Usage: print_kv "Key" "Value" [color]
print_kv() {
    local key="$1"
    local value="$2"
    local color="${3:-$WHITE}"
    
    printf "  ${GRAY}%-20s${NC} ${color}%s${NC}\n" "$key:" "$value"
}

# Print environment variable
# Usage: print_env "VAR_NAME" "value" [masked]
print_env() {
    local name="$1"
    local value="$2"
    local masked="${3:-false}"
    
    if [[ "$masked" == "true" ]]; then
        local len=${#value}
        if [[ $len -gt 8 ]]; then
            value="${value:0:4}$( printf '*%.0s' {1..20} )${value: -4}"
        else
            value="********"
        fi
    fi
    
    printf "  ${CYAN}%-30s${NC} = ${YELLOW}%s${NC}\n" "$name" "$value"
}

# ============================================================================
# STATUS INDICATORS
# ============================================================================

# Print status with icon
# Usage: print_status "success|error|warning|info|pending" "message"
print_status() {
    local status="$1"
    local message="$2"
    
    case "$status" in
        success|ok|pass|healthy)
            echo -e "  ${GREEN}${SYM_CHECK}${NC}  ${GREEN}$message${NC}"
            ;;
        error|fail|failed|unhealthy)
            echo -e "  ${RED}${SYM_CROSS}${NC}  ${RED}$message${NC}"
            ;;
        warning|warn|degraded)
            echo -e "  ${YELLOW}${SYM_WARN}${NC}  ${YELLOW}$message${NC}"
            ;;
        info)
            echo -e "  ${BLUE}${SYM_INFO}${NC}  $message"
            ;;
        pending|waiting)
            echo -e "  ${GRAY}○${NC}  ${GRAY}$message${NC}"
            ;;
        running|active)
            echo -e "  ${CYAN}◉${NC}  ${CYAN}$message${NC}"
            ;;
        *)
            echo -e "  ${GRAY}•${NC}  $message"
            ;;
    esac
}

# ============================================================================
# URL DISPLAY
# ============================================================================

# Print a clickable URL
# Usage: print_url "Label" "https://example.com"
print_url() {
    local label="$1"
    local url="$2"
    
    printf "  ${GRAY}%-15s${NC} ${BRIGHT_CYAN}${UNDERLINE}%s${NC}\n" "$label:" "$url"
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

export -f start_spinner stop_spinner
export -f init_stages print_stage_header next_stage stage_complete stage_failed
export -f gradient_progress
export -f print_deploy_banner print_vercel_banner print_render_banner
export -f print_success_banner print_error_banner
export -f print_table print_kv print_env print_status print_url

log DEBUG "Nexus UI library loaded"

