#!/usr/bin/env bash
# ============================================================================
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                                                                           ║
# ║   🚀 NEXUS RELEASE AUTOMATION - UNIFIED DEPLOYMENT SCRIPT v3.0          ║
# ║                                                                           ║
# ║   One-click deployment to Vercel (Frontend) and Render (Backend)         ║
# ║                                                                           ║
# ║   Features:                                                               ║
# ║     • REST API-based configuration (no UI needed)                        ║
# ║     • Automatic project creation                                         ║
# ║     • Environment variable management                                    ║
# ║     • CORS configuration                                                 ║
# ║     • Auto-deployment on git commits                                     ║
# ║     • Force deployment on latest commit                                  ║
# ║     • Git author issue workarounds                                       ║
# ║                                                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# ============================================================================

# Script identification
NEXUS_SCRIPT_NAME="deploy"
NEXUS_SCRIPT_VERSION="3.0.0"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source libraries
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/network.sh"
source "$SCRIPT_DIR/lib/ui.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

# Project configuration
GITHUB_REPO="${GITHUB_REPO:-IKRedHat/Nexus-Release-Readiness-Bot}"
GITHUB_BRANCH="${GITHUB_BRANCH:-main}"

# Frontend configuration
FRONTEND_DIR="services/admin_dashboard/frontend-next"
FRONTEND_NAME="nexus-admin-dashboard"
FRONTEND_FRAMEWORK="nextjs"
NODE_VERSION="20.x"

# Backend configuration
BACKEND_DIR="services/admin_dashboard/backend"
BACKEND_NAME="nexus-admin-api"

# API endpoints
VERCEL_API="https://api.vercel.com"
RENDER_API="https://api.render.com/v1"

# Environment variables for frontend
declare -A FRONTEND_ENV_VARS=(
    ["NEXT_PUBLIC_API_URL"]=""
    ["NEXT_PUBLIC_APP_NAME"]="Nexus Admin Dashboard"
    ["NEXT_PUBLIC_VERSION"]="2.6.0"
)

# Environment variables for backend
declare -A BACKEND_ENV_VARS=(
    ["NEXUS_ENV"]="production"
    ["NEXUS_MOCK_MODE"]="false"
    ["LOG_LEVEL"]="INFO"
    ["NEXUS_JWT_SECRET"]=""
    ["NEXUS_CORS_ORIGINS"]=""
    ["REDIS_URL"]=""
    ["LLM_PROVIDER"]="google"
    ["LLM_MODEL"]="gemini-2.0-flash"
    ["GEMINI_API_KEY"]=""
)

# State
VERCEL_PROJECT_ID=""
RENDER_SERVICE_ID=""
BACKEND_URL=""
FRONTEND_URL=""

# ============================================================================
# API UTILITIES
# ============================================================================

# Make authenticated API request to Vercel
vercel_api() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"
    
    local url="${VERCEL_API}${endpoint}"
    local args=(-s -X "$method" -H "Authorization: Bearer $VERCEL_TOKEN" -H "Content-Type: application/json")
    
    if [[ -n "$data" ]]; then
        args+=(-d "$data")
    fi
    
    curl "${args[@]}" "$url" 2>/dev/null
}

# Make authenticated API request to Render
render_api() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"
    
    local url="${RENDER_API}${endpoint}"
    local args=(-s -X "$method" -H "Authorization: Bearer $RENDER_TOKEN" -H "Content-Type: application/json")
    
    if [[ -n "$data" ]]; then
        args+=(-d "$data")
    fi
    
    curl "${args[@]}" "$url" 2>/dev/null
}

# Extract JSON value
json_value() {
    local json="$1"
    local key="$2"
    echo "$json" | grep -o "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | sed 's/.*: *"\([^"]*\)".*/\1/' | head -1
}

# ============================================================================
# TOKEN VALIDATION
# ============================================================================

validate_tokens() {
    log SUBSTEP "Validating API tokens..."
    echo ""
    
    local all_valid=true
    
    # Check Vercel token
    echo -ne "  ${WHITE}→${NC} Vercel API Token... "
    if [[ -z "$VERCEL_TOKEN" ]]; then
        echo -e "${RED}✗ Not set${NC}"
        all_valid=false
    else
        local vercel_user
        vercel_user=$(vercel_api GET "/v2/user")
        local username
        username=$(json_value "$vercel_user" "username")
        
        if [[ -n "$username" ]]; then
            echo -e "${GREEN}✓${NC} ${GRAY}(user: $username)${NC}"
        else
            echo -e "${RED}✗ Invalid${NC}"
            all_valid=false
        fi
    fi
    
    # Check Render token
    echo -ne "  ${WHITE}→${NC} Render API Token... "
    if [[ -z "$RENDER_TOKEN" ]]; then
        echo -e "${RED}✗ Not set${NC}"
        all_valid=false
    else
        local render_user
        render_user=$(render_api GET "/owners")
        
        if [[ "$render_user" == *"owner"* ]] || [[ "$render_user" == *"id"* ]]; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗ Invalid${NC}"
            all_valid=false
        fi
    fi
    
    # Check GitHub token (optional but recommended)
    echo -ne "  ${WHITE}→${NC} GitHub Token... "
    if [[ -z "$GITHUB_TOKEN" ]]; then
        echo -e "${YELLOW}⚠ Not set (optional)${NC}"
    else
        echo -e "${GREEN}✓${NC}"
    fi
    
    echo ""
    
    if ! $all_valid; then
        log ERROR "Missing or invalid API tokens"
        echo ""
        echo -e "  ${YELLOW}Please set the following environment variables:${NC}"
        echo ""
        echo -e "  ${CYAN}export VERCEL_TOKEN=\"your-vercel-token\"${NC}"
        echo -e "    Get from: https://vercel.com/account/tokens"
        echo ""
        echo -e "  ${CYAN}export RENDER_TOKEN=\"your-render-api-key\"${NC}"
        echo -e "    Get from: https://dashboard.render.com/u/YOUR_USER/settings#api-keys"
        echo ""
        return 1
    fi
    
    return 0
}

# ============================================================================
# VERCEL DEPLOYMENT
# ============================================================================

vercel_create_project() {
    log SUBSTEP "Creating/updating Vercel project..."
    
    # Check if project exists
    local projects
    projects=$(vercel_api GET "/v9/projects")
    
    if echo "$projects" | grep -q "\"name\":\"$FRONTEND_NAME\""; then
        VERCEL_PROJECT_ID=$(echo "$projects" | grep -o "\"id\":\"[^\"]*\"" | head -1 | cut -d'"' -f4)
        log INFO "Project already exists (ID: $VERCEL_PROJECT_ID)"
    else
        log INFO "Creating new project: $FRONTEND_NAME"
        
        local create_response
        create_response=$(vercel_api POST "/v10/projects" "{
            \"name\": \"$FRONTEND_NAME\",
            \"framework\": \"$FRONTEND_FRAMEWORK\",
            \"gitRepository\": {
                \"type\": \"github\",
                \"repo\": \"$GITHUB_REPO\"
            },
            \"rootDirectory\": \"$FRONTEND_DIR\",
            \"buildCommand\": \"npm run build\",
            \"outputDirectory\": \".next\",
            \"installCommand\": \"npm install --legacy-peer-deps\"
        }")
        
        VERCEL_PROJECT_ID=$(json_value "$create_response" "id")
        
        if [[ -n "$VERCEL_PROJECT_ID" ]]; then
            stage_complete "Project created: $VERCEL_PROJECT_ID"
        else
            stage_failed "Failed to create project"
            echo "$create_response"
            return 1
        fi
    fi
}

vercel_set_env_vars() {
    log SUBSTEP "Setting environment variables..."
    echo ""
    
    for var_name in "${!FRONTEND_ENV_VARS[@]}"; do
        local var_value="${FRONTEND_ENV_VARS[$var_name]}"
        
        # Skip empty values
        if [[ -z "$var_value" ]]; then
            continue
        fi
        
        echo -ne "  ${WHITE}→${NC} Setting $var_name... "
        
        # Delete existing if present
        vercel_api DELETE "/v10/projects/$VERCEL_PROJECT_ID/env/$var_name" &>/dev/null
        
        # Create new
        local response
        response=$(vercel_api POST "/v10/projects/$VERCEL_PROJECT_ID/env" "{
            \"key\": \"$var_name\",
            \"value\": \"$var_value\",
            \"type\": \"encrypted\",
            \"target\": [\"production\", \"preview\", \"development\"]
        }")
        
        if echo "$response" | grep -q "\"key\":\"$var_name\""; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠${NC}"
        fi
    done
    
    echo ""
}

vercel_configure_settings() {
    log SUBSTEP "Configuring project settings..."
    
    # Set Node.js version and other settings
    local settings_response
    settings_response=$(vercel_api PATCH "/v9/projects/$VERCEL_PROJECT_ID" "{
        \"nodeVersion\": \"$NODE_VERSION\",
        \"framework\": \"$FRONTEND_FRAMEWORK\",
        \"buildCommand\": \"npm run build\",
        \"outputDirectory\": \".next\",
        \"installCommand\": \"npm install --legacy-peer-deps\",
        \"rootDirectory\": \"$FRONTEND_DIR\"
    }")
    
    if echo "$settings_response" | grep -q "\"id\""; then
        stage_complete "Project settings updated"
    else
        stage_failed "Failed to update settings"
    fi
    
    # Enable auto-deployment
    log SUBSTEP "Enabling auto-deployment on git push..."
    
    local git_config
    git_config=$(vercel_api PATCH "/v9/projects/$VERCEL_PROJECT_ID" "{
        \"autoExposeSystemEnvs\": true,
        \"gitForkProtection\": false
    }")
    
    stage_complete "Auto-deployment configured"
}

vercel_trigger_deployment() {
    log SUBSTEP "Triggering deployment..."
    
    # Get latest commit
    local latest_commit
    latest_commit=$(git -C "$NEXUS_PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo "main")
    
    log INFO "Deploying commit: ${latest_commit:0:8}"
    
    # Create deployment
    local deploy_response
    deploy_response=$(vercel_api POST "/v13/deployments" "{
        \"name\": \"$FRONTEND_NAME\",
        \"project\": \"$VERCEL_PROJECT_ID\",
        \"target\": \"production\",
        \"gitSource\": {
            \"type\": \"github\",
            \"repoId\": \"$GITHUB_REPO\",
            \"ref\": \"$GITHUB_BRANCH\",
            \"sha\": \"$latest_commit\"
        }
    }")
    
    local deploy_id
    deploy_id=$(json_value "$deploy_response" "id")
    local deploy_url
    deploy_url=$(json_value "$deploy_response" "url")
    
    if [[ -n "$deploy_id" ]]; then
        FRONTEND_URL="https://$deploy_url"
        stage_complete "Deployment initiated: $deploy_id"
        
        # Wait for deployment
        log SUBSTEP "Waiting for deployment to complete..."
        
        local status="BUILDING"
        local attempts=0
        local max_attempts=60
        
        while [[ "$status" != "READY" ]] && [[ "$status" != "ERROR" ]] && [[ $attempts -lt $max_attempts ]]; do
            sleep 10
            ((attempts++))
            
            local deploy_status
            deploy_status=$(vercel_api GET "/v13/deployments/$deploy_id")
            status=$(json_value "$deploy_status" "readyState")
            
            gradient_progress $attempts $max_attempts "Building ($status)"
        done
        
        echo ""
        
        if [[ "$status" == "READY" ]]; then
            stage_complete "Deployment successful!"
            return 0
        else
            stage_failed "Deployment failed: $status"
            return 1
        fi
    else
        stage_failed "Failed to trigger deployment"
        echo "$deploy_response"
        return 1
    fi
}

# ============================================================================
# RENDER DEPLOYMENT
# ============================================================================

render_create_service() {
    log SUBSTEP "Creating/updating Render service..."
    
    # List services
    local services
    services=$(render_api GET "/services")
    
    if echo "$services" | grep -q "\"name\":\"$BACKEND_NAME\""; then
        RENDER_SERVICE_ID=$(echo "$services" | grep -B10 "\"name\":\"$BACKEND_NAME\"" | grep -o "\"id\":\"[^\"]*\"" | head -1 | cut -d'"' -f4)
        log INFO "Service already exists (ID: $RENDER_SERVICE_ID)"
    else
        log INFO "Creating new service: $BACKEND_NAME"
        
        local create_response
        create_response=$(render_api POST "/services" "{
            \"type\": \"web_service\",
            \"name\": \"$BACKEND_NAME\",
            \"ownerId\": \"$(render_api GET "/owners" | grep -o "\"id\":\"[^\"]*\"" | head -1 | cut -d'"' -f4)\",
            \"repo\": \"https://github.com/$GITHUB_REPO\",
            \"branch\": \"$GITHUB_BRANCH\",
            \"rootDir\": \"$BACKEND_DIR\",
            \"runtime\": \"python\",
            \"buildCommand\": \"pip install -r requirements.txt\",
            \"startCommand\": \"uvicorn main:app --host 0.0.0.0 --port \$PORT\",
            \"plan\": \"starter\",
            \"autoDeploy\": \"yes\"
        }")
        
        RENDER_SERVICE_ID=$(json_value "$create_response" "id")
        
        if [[ -n "$RENDER_SERVICE_ID" ]]; then
            stage_complete "Service created: $RENDER_SERVICE_ID"
        else
            stage_failed "Failed to create service"
            echo "$create_response"
            return 1
        fi
    fi
    
    # Get service URL
    local service_info
    service_info=$(render_api GET "/services/$RENDER_SERVICE_ID")
    BACKEND_URL=$(echo "$service_info" | grep -o "\"url\":\"[^\"]*\"" | cut -d'"' -f4)
    
    if [[ -z "$BACKEND_URL" ]]; then
        BACKEND_URL="https://${BACKEND_NAME}.onrender.com"
    fi
    
    log INFO "Backend URL: $BACKEND_URL"
}

render_set_env_vars() {
    log SUBSTEP "Setting environment variables..."
    echo ""
    
    # Build environment variables list
    local env_vars="["
    local first=true
    
    for var_name in "${!BACKEND_ENV_VARS[@]}"; do
        local var_value="${BACKEND_ENV_VARS[$var_name]}"
        
        # Skip empty values (except CORS which we'll set later)
        if [[ -z "$var_value" ]] && [[ "$var_name" != "NEXUS_CORS_ORIGINS" ]]; then
            continue
        fi
        
        # Special handling for CORS
        if [[ "$var_name" == "NEXUS_CORS_ORIGINS" ]]; then
            var_value="$FRONTEND_URL,https://$FRONTEND_NAME.vercel.app,https://*.vercel.app,http://localhost:3000"
        fi
        
        if ! $first; then
            env_vars+=","
        fi
        first=false
        
        env_vars+="{\"key\":\"$var_name\",\"value\":\"$var_value\"}"
        print_env "$var_name" "$var_value" true
    done
    
    env_vars+="]"
    
    echo ""
    
    # Update environment variables
    local response
    response=$(render_api PUT "/services/$RENDER_SERVICE_ID/env-vars" "$env_vars")
    
    if echo "$response" | grep -q "key"; then
        stage_complete "Environment variables updated"
    else
        stage_failed "Failed to update environment variables"
        return 1
    fi
}

render_update_cors() {
    log SUBSTEP "Updating CORS configuration..."
    
    # Build CORS origins list
    local cors_origins="$FRONTEND_URL,https://$FRONTEND_NAME.vercel.app,https://*.vercel.app,http://localhost:3000"
    
    print_kv "CORS Origins" "$cors_origins"
    
    # Update the specific CORS environment variable
    local response
    response=$(render_api PUT "/services/$RENDER_SERVICE_ID/env-vars" "[
        {\"key\":\"NEXUS_CORS_ORIGINS\",\"value\":\"$cors_origins\"}
    ]")
    
    stage_complete "CORS configured for frontend domains"
}

render_trigger_deployment() {
    log SUBSTEP "Triggering deployment..."
    
    local deploy_response
    deploy_response=$(render_api POST "/services/$RENDER_SERVICE_ID/deploys" "{
        \"clearCache\": \"clear\"
    }")
    
    local deploy_id
    deploy_id=$(json_value "$deploy_response" "id")
    
    if [[ -n "$deploy_id" ]]; then
        stage_complete "Deployment initiated: $deploy_id"
        
        # Wait for deployment
        log SUBSTEP "Waiting for deployment to complete..."
        
        local status="created"
        local attempts=0
        local max_attempts=60
        
        while [[ "$status" != "live" ]] && [[ "$status" != "deactivated" ]] && [[ $attempts -lt $max_attempts ]]; do
            sleep 10
            ((attempts++))
            
            local deploy_status
            deploy_status=$(render_api GET "/services/$RENDER_SERVICE_ID/deploys/$deploy_id")
            status=$(json_value "$deploy_status" "status")
            
            gradient_progress $attempts $max_attempts "Building ($status)"
        done
        
        echo ""
        
        if [[ "$status" == "live" ]]; then
            stage_complete "Deployment successful!"
            return 0
        else
            stage_failed "Deployment failed: $status"
            return 1
        fi
    else
        stage_failed "Failed to trigger deployment"
        return 1
    fi
}

render_enable_auto_deploy() {
    log SUBSTEP "Enabling auto-deployment..."
    
    local response
    response=$(render_api PATCH "/services/$RENDER_SERVICE_ID" "{
        \"autoDeploy\": \"yes\"
    }")
    
    if echo "$response" | grep -q "autoDeploy"; then
        stage_complete "Auto-deployment enabled"
    else
        stage_failed "Failed to enable auto-deployment"
    fi
}

# ============================================================================
# FULL DEPLOYMENT FLOW
# ============================================================================

deploy_backend() {
    next_stage
    
    render_create_service || return 1
    render_set_env_vars || return 1
    render_enable_auto_deploy || return 1
    render_trigger_deployment || return 1
}

deploy_frontend() {
    next_stage
    
    # Update frontend env with backend URL
    FRONTEND_ENV_VARS["NEXT_PUBLIC_API_URL"]="$BACKEND_URL"
    
    vercel_create_project || return 1
    vercel_set_env_vars || return 1
    vercel_configure_settings || return 1
    vercel_trigger_deployment || return 1
}

update_cors() {
    next_stage
    
    render_update_cors || return 1
}

# ============================================================================
# INTERACTIVE MENU
# ============================================================================

show_deploy_menu() {
    print_deploy_banner
    
    echo -e "  ${WHITE}What would you like to deploy?${NC}"
    echo ""
    echo -e "    ${GREEN}[1]${NC}  🚀 Full Deployment (Backend + Frontend + CORS)"
    echo -e "    ${CYAN}[2]${NC}  🔧 Backend Only (Render)"
    echo -e "    ${CYAN}[3]${NC}  🎨 Frontend Only (Vercel)"
    echo -e "    ${YELLOW}[4]${NC}  🔐 Update CORS Only"
    echo -e "    ${YELLOW}[5]${NC}  📋 Update Environment Variables Only"
    echo -e "    ${GRAY}[6]${NC}  🔍 Check Deployment Status"
    echo ""
    echo -e "    ${RED}[0]${NC}  Exit"
    echo ""
    echo -ne "  Enter your choice: "
}

show_status() {
    log STEP "Deployment Status"
    
    echo ""
    echo -e "  ${CYAN}Backend (Render)${NC}"
    
    if [[ -n "$RENDER_SERVICE_ID" ]] || [[ -n "$RENDER_TOKEN" ]]; then
        local services
        services=$(render_api GET "/services")
        
        if echo "$services" | grep -q "\"name\":\"$BACKEND_NAME\""; then
            local service_info
            service_info=$(echo "$services" | grep -A20 "\"name\":\"$BACKEND_NAME\"")
            
            print_status "success" "Service exists: $BACKEND_NAME"
            print_url "URL" "$(echo "$service_info" | grep -o "\"url\":\"[^\"]*\"" | cut -d'"' -f4 || echo 'https://${BACKEND_NAME}.onrender.com')"
        else
            print_status "pending" "Service not found"
        fi
    else
        print_status "pending" "Render token not set"
    fi
    
    echo ""
    echo -e "  ${CYAN}Frontend (Vercel)${NC}"
    
    if [[ -n "$VERCEL_PROJECT_ID" ]] || [[ -n "$VERCEL_TOKEN" ]]; then
        local projects
        projects=$(vercel_api GET "/v9/projects")
        
        if echo "$projects" | grep -q "\"name\":\"$FRONTEND_NAME\""; then
            print_status "success" "Project exists: $FRONTEND_NAME"
            
            # Get latest deployment
            local deployments
            deployments=$(vercel_api GET "/v6/deployments?projectId=$VERCEL_PROJECT_ID&limit=1")
            local deploy_url
            deploy_url=$(json_value "$deployments" "url")
            
            if [[ -n "$deploy_url" ]]; then
                print_url "URL" "https://$deploy_url"
            fi
        else
            print_status "pending" "Project not found"
        fi
    else
        print_status "pending" "Vercel token not set"
    fi
    
    echo ""
}

update_env_only() {
    log STEP "Update Environment Variables"
    
    echo ""
    echo -e "  ${WHITE}Select platform:${NC}"
    echo ""
    echo -e "    ${GREEN}[1]${NC}  Vercel (Frontend)"
    echo -e "    ${GREEN}[2]${NC}  Render (Backend)"
    echo -e "    ${GREEN}[3]${NC}  Both"
    echo ""
    echo -ne "  Choice: "
    read -r platform_choice
    
    case "$platform_choice" in
        1)
            validate_tokens || return 1
            vercel_create_project || return 1
            vercel_set_env_vars
            ;;
        2)
            validate_tokens || return 1
            render_create_service || return 1
            render_set_env_vars
            ;;
        3)
            validate_tokens || return 1
            vercel_create_project || return 1
            render_create_service || return 1
            vercel_set_env_vars
            render_set_env_vars
            ;;
    esac
}

# ============================================================================
# MAIN DEPLOYMENT
# ============================================================================

full_deployment() {
    print_deploy_banner
    
    # Initialize stages
    init_stages "Validate Tokens" "Deploy Backend (Render)" "Deploy Frontend (Vercel)" "Update CORS Configuration" "Verification"
    print_stage_header
    
    # Stage 1: Validate
    next_stage
    if ! validate_tokens; then
        print_error_banner "Token validation failed"
        return 1
    fi
    stage_complete "All tokens validated"
    
    # Stage 2: Backend
    deploy_backend || {
        print_error_banner "Backend deployment failed"
        return 1
    }
    
    # Stage 3: Frontend
    deploy_frontend || {
        print_error_banner "Frontend deployment failed"
        return 1
    }
    
    # Stage 4: CORS
    update_cors || {
        print_error_banner "CORS update failed"
        return 1
    }
    
    # Stage 5: Verification
    next_stage
    
    echo ""
    log SUBSTEP "Verifying deployments..."
    
    # Check backend
    echo -ne "  ${WHITE}→${NC} Backend health check... "
    if check_url "$BACKEND_URL/health" "200" 10 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ Starting up...${NC}"
    fi
    
    # Check frontend
    echo -ne "  ${WHITE}→${NC} Frontend accessibility... "
    if check_url "$FRONTEND_URL" "200" 10 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}⚠ Building...${NC}"
    fi
    
    stage_complete "Verification complete"
    
    # Summary
    print_success_banner "Deployment Complete!"
    
    echo ""
    echo -e "  ${CYAN}Deployed URLs:${NC}"
    print_url "Backend API" "$BACKEND_URL"
    print_url "Frontend App" "$FRONTEND_URL"
    print_url "API Docs" "$BACKEND_URL/docs"
    echo ""
    
    echo -e "  ${CYAN}Configuration:${NC}"
    print_kv "Auto-Deploy" "Enabled (on git push)"
    print_kv "CORS" "Configured"
    print_kv "Node.js" "$NODE_VERSION"
    echo ""
    
    echo -e "  ${YELLOW}Next Steps:${NC}"
    echo -e "    1. Wait 2-3 minutes for services to fully start"
    echo -e "    2. Visit the Frontend URL to test"
    echo -e "    3. Check API docs at $BACKEND_URL/docs"
    echo ""
}

# ============================================================================
# CLI INTERFACE
# ============================================================================

show_help() {
    print_help_header "nexus deploy.sh" "$NEXUS_SCRIPT_VERSION" "Unified Deployment Script"
    
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./scripts/deploy.sh [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo "  all              Full deployment (backend + frontend + CORS)"
    echo "  backend          Deploy backend to Render only"
    echo "  frontend         Deploy frontend to Vercel only"
    echo "  cors             Update CORS configuration only"
    echo "  env              Update environment variables only"
    echo "  status           Check deployment status"
    echo "  help             Show this help"
    echo ""
    echo -e "${CYAN}Required Environment Variables:${NC}"
    echo "  VERCEL_TOKEN     Vercel API token"
    echo "  RENDER_TOKEN     Render API key"
    echo ""
    echo -e "${CYAN}Optional Environment Variables:${NC}"
    echo "  GITHUB_TOKEN     GitHub personal access token"
    echo "  GITHUB_REPO      Repository (default: IKRedHat/Nexus-Release-Readiness-Bot)"
    echo "  GITHUB_BRANCH    Branch to deploy (default: main)"
    echo ""
    echo -e "${CYAN}Backend Environment Variables:${NC}"
    for var in "${!BACKEND_ENV_VARS[@]}"; do
        echo "  $var"
    done
    echo ""
    echo -e "${CYAN}Frontend Environment Variables:${NC}"
    for var in "${!FRONTEND_ENV_VARS[@]}"; do
        echo "  $var"
    done
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./scripts/deploy.sh                    # Interactive mode"
    echo "  ./scripts/deploy.sh all                # Full deployment"
    echo "  ./scripts/deploy.sh backend            # Backend only"
    echo "  ./scripts/deploy.sh status             # Check status"
    echo ""
    echo -e "${CYAN}Getting API Tokens:${NC}"
    echo "  Vercel:  https://vercel.com/account/tokens"
    echo "  Render:  https://dashboard.render.com/u/YOUR_USER/settings#api-keys"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    local command="${1:-}"
    shift 2>/dev/null || true
    
    case "$command" in
        all)
            full_deployment
            ;;
        backend)
            print_deploy_banner
            init_stages "Validate Tokens" "Deploy Backend (Render)"
            print_stage_header
            next_stage
            validate_tokens || exit 1
            stage_complete "Tokens validated"
            deploy_backend
            ;;
        frontend)
            print_deploy_banner
            init_stages "Validate Tokens" "Deploy Frontend (Vercel)"
            print_stage_header
            next_stage
            validate_tokens || exit 1
            stage_complete "Tokens validated"
            
            # Need backend URL
            echo -ne "  ${CYAN}?${NC}  Enter Backend URL: "
            read -r BACKEND_URL
            FRONTEND_ENV_VARS["NEXT_PUBLIC_API_URL"]="$BACKEND_URL"
            
            deploy_frontend
            ;;
        cors)
            print_deploy_banner
            validate_tokens || exit 1
            
            echo -ne "  ${CYAN}?${NC}  Enter Frontend URL: "
            read -r FRONTEND_URL
            
            render_create_service || exit 1
            render_update_cors
            render_trigger_deployment
            ;;
        env)
            update_env_only
            ;;
        status)
            print_deploy_banner
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            # Interactive mode
            while true; do
                show_deploy_menu
                read -r choice
                
                case "$choice" in
                    1) full_deployment; break ;;
                    2) 
                        print_deploy_banner
                        init_stages "Validate Tokens" "Deploy Backend (Render)"
                        print_stage_header
                        next_stage
                        validate_tokens || continue
                        stage_complete "Tokens validated"
                        deploy_backend
                        break
                        ;;
                    3)
                        print_deploy_banner
                        init_stages "Validate Tokens" "Deploy Frontend (Vercel)"
                        print_stage_header
                        next_stage
                        validate_tokens || continue
                        stage_complete "Tokens validated"
                        echo -ne "  ${CYAN}?${NC}  Enter Backend URL: "
                        read -r BACKEND_URL
                        FRONTEND_ENV_VARS["NEXT_PUBLIC_API_URL"]="$BACKEND_URL"
                        deploy_frontend
                        break
                        ;;
                    4)
                        print_deploy_banner
                        validate_tokens || continue
                        echo -ne "  ${CYAN}?${NC}  Enter Frontend URL: "
                        read -r FRONTEND_URL
                        render_create_service || continue
                        render_update_cors
                        render_trigger_deployment
                        break
                        ;;
                    5) update_env_only; break ;;
                    6) show_status ;;
                    0) 
                        echo -e "\n  ${GREEN}Goodbye! 👋${NC}\n"
                        exit 0
                        ;;
                    *)
                        log WARNING "Invalid option"
                        sleep 1
                        ;;
                esac
            done
            ;;
        *)
            log ERROR "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run
main "$@"

