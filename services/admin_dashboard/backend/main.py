"""
Nexus Admin Dashboard - Backend API
====================================

FastAPI backend for the Admin Dashboard providing:
- System configuration management (Redis-backed)
- Agent health monitoring
- Mode switching (Mock/Live)
- Secure credential management

Author: Nexus Team
Version: 2.3.0
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Add shared lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'shared'))

try:
    from nexus_lib.config import (
        ConfigManager, ConfigKeys, RedisConnection, AgentRegistry,
        SENSITIVE_KEYS, DEFAULT_CONFIG, ENV_VAR_MAPPING
    )
except ImportError:
    # Fallback for standalone operation
    ConfigManager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Prometheus Metrics
# =============================================================================

CONFIG_CHANGES = Counter(
    "nexus_admin_config_changes_total",
    "Total configuration changes",
    ["key", "source"]
)
HEALTH_CHECKS = Counter(
    "nexus_admin_health_checks_total",
    "Total health checks performed",
    ["agent", "status"]
)
MODE_SWITCHES = Counter(
    "nexus_admin_mode_switches_total",
    "Total mode switches",
    ["from_mode", "to_mode"]
)
ACTIVE_MODE = Gauge(
    "nexus_admin_active_mode",
    "Current system mode (0=mock, 1=live)"
)

# =============================================================================
# Pydantic Models
# =============================================================================

class SystemMode(BaseModel):
    """System mode configuration."""
    mode: str = Field(..., pattern="^(mock|live)$", description="System mode: 'mock' or 'live'")


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    key: str = Field(..., description="Configuration key")
    value: str = Field(..., description="Configuration value")


class BulkConfigUpdate(BaseModel):
    """Bulk configuration update."""
    config: Dict[str, str] = Field(..., description="Key-value pairs to update")


class ConfigResponse(BaseModel):
    """Configuration response with masked secrets."""
    key: str
    value: str
    masked_value: str
    is_sensitive: bool
    source: str  # "redis", "env", "default"
    last_updated: Optional[datetime] = None


class AgentHealth(BaseModel):
    """Agent health status."""
    agent_id: str
    name: str
    url: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    last_checked: datetime


class SystemHealth(BaseModel):
    """Overall system health."""
    status: str  # "healthy", "degraded", "unhealthy"
    mode: str
    agents: List[AgentHealth]
    healthy_count: int
    total_count: int
    timestamp: datetime


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    mode: str
    config_count: int
    healthy_agents: int
    total_agents: int
    redis_connected: bool
    uptime_seconds: float


# =============================================================================
# Application Setup
# =============================================================================

START_TIME = datetime.utcnow()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting Nexus Admin Dashboard Backend...")
    
    # Test Redis connection
    try:
        redis = await RedisConnection().get_client()
        if redis:
            logger.info("✅ Connected to Redis")
    except Exception as e:
        logger.warning(f"⚠️ Redis not available: {e}")
    
    yield
    
    # Cleanup
    await RedisConnection().close()
    logger.info("👋 Admin Dashboard Backend shutdown complete")


app = FastAPI(
    title="Nexus Admin Dashboard API",
    description="Backend API for managing Nexus system configuration and monitoring",
    version="2.3.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to dashboard URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Status Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Backend health check."""
    return {
        "status": "healthy",
        "service": "admin-dashboard-backend",
        "version": "2.3.0",
        "timestamp": datetime.utcnow().isoformat(),
        "redis_connected": RedisConnection().is_connected
    }


@app.get("/metrics")
async def prometheus_metrics():
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics."""
    mode = await ConfigManager.get_mode() if ConfigManager else "mock"
    config = await ConfigManager.get_all() if ConfigManager else {}
    
    # Quick health check
    agents = AgentRegistry.get_all_agents() if ConfigManager else {}
    healthy = 0
    total = len(agents)
    
    uptime = (datetime.utcnow() - START_TIME).total_seconds()
    
    return DashboardStats(
        mode=mode,
        config_count=len(config),
        healthy_agents=healthy,
        total_agents=total,
        redis_connected=RedisConnection().is_connected if ConfigManager else False,
        uptime_seconds=uptime
    )


# =============================================================================
# Mode Management
# =============================================================================

@app.get("/mode")
async def get_system_mode():
    """Get current system mode."""
    if not ConfigManager:
        return {"mode": "mock", "source": "default"}
    
    mode = await ConfigManager.get_mode()
    ACTIVE_MODE.set(1 if mode == "live" else 0)
    
    return {
        "mode": mode,
        "is_mock": mode == "mock",
        "is_live": mode == "live"
    }


@app.post("/mode")
async def set_system_mode(mode_request: SystemMode):
    """
    Switch system mode between 'mock' and 'live'.
    
    This affects ALL agents in the system.
    """
    if not ConfigManager:
        raise HTTPException(500, "Configuration manager not available")
    
    current_mode = await ConfigManager.get_mode()
    new_mode = mode_request.mode
    
    if current_mode == new_mode:
        return {"message": f"System already in {new_mode} mode", "mode": new_mode}
    
    success = await ConfigManager.set_mode(new_mode)
    
    if success:
        MODE_SWITCHES.labels(from_mode=current_mode, to_mode=new_mode).inc()
        ACTIVE_MODE.set(1 if new_mode == "live" else 0)
        logger.info(f"System mode switched: {current_mode} -> {new_mode}")
        
        return {
            "message": f"System mode switched to {new_mode}",
            "previous_mode": current_mode,
            "current_mode": new_mode
        }
    else:
        raise HTTPException(500, "Failed to update system mode")


# =============================================================================
# Configuration Management
# =============================================================================

@app.get("/config")
async def get_all_config():
    """
    Get all configuration values.
    
    Sensitive values are masked for security.
    """
    if not ConfigManager:
        return {"config": {}, "mode": "mock"}
    
    config = await ConfigManager.get_all()
    mode = await ConfigManager.get_mode()
    
    # Prepare response with masked values
    result = []
    for key, value in config.items():
        is_sensitive = ConfigManager.is_sensitive(key)
        masked_value = ConfigManager.mask_value(key, value) if value else ""
        
        # Determine source
        source = "redis"
        env_var = ENV_VAR_MAPPING.get(key)
        if env_var and os.environ.get(env_var):
            source = "env" if value == os.environ.get(env_var) else "redis"
        elif key in DEFAULT_CONFIG and value == DEFAULT_CONFIG[key]:
            source = "default"
        
        result.append({
            "key": key,
            "value": value if not is_sensitive else None,
            "masked_value": masked_value,
            "is_sensitive": is_sensitive,
            "source": source,
            "env_var": env_var,
            "category": _get_category(key)
        })
    
    return {
        "config": result,
        "mode": mode,
        "count": len(result)
    }


@app.get("/config/{key:path}")
async def get_config_value(key: str):
    """Get a specific configuration value."""
    if not ConfigManager:
        raise HTTPException(500, "Configuration manager not available")
    
    value = await ConfigManager.get(key)
    
    if value is None:
        raise HTTPException(404, f"Configuration key not found: {key}")
    
    is_sensitive = ConfigManager.is_sensitive(key)
    
    return {
        "key": key,
        "value": value if not is_sensitive else None,
        "masked_value": ConfigManager.mask_value(key, value),
        "is_sensitive": is_sensitive
    }


@app.post("/config")
async def update_config(update: ConfigUpdate):
    """
    Update a configuration value.
    
    The value is stored in Redis for dynamic configuration.
    """
    if not ConfigManager:
        raise HTTPException(500, "Configuration manager not available")
    
    # Validate key format
    if not update.key.startswith("nexus:"):
        raise HTTPException(400, "Invalid key format. Keys must start with 'nexus:'")
    
    # Don't allow empty values for sensitive keys
    if ConfigManager.is_sensitive(update.key) and not update.value:
        raise HTTPException(400, "Cannot set empty value for sensitive configuration")
    
    success = await ConfigManager.set(update.key, update.value)
    
    if success:
        CONFIG_CHANGES.labels(key=update.key, source="admin_ui").inc()
        logger.info(f"Config updated via admin UI: {ConfigManager._mask_key(update.key)}")
        
        return {
            "message": "Configuration updated successfully",
            "key": update.key,
            "masked_value": ConfigManager.mask_value(update.key, update.value)
        }
    else:
        raise HTTPException(500, "Failed to update configuration")


@app.post("/config/bulk")
async def update_config_bulk(update: BulkConfigUpdate):
    """Update multiple configuration values at once."""
    if not ConfigManager:
        raise HTTPException(500, "Configuration manager not available")
    
    success = await ConfigManager.set_bulk(update.config)
    
    if success:
        for key in update.config.keys():
            CONFIG_CHANGES.labels(key=key, source="admin_ui_bulk").inc()
        
        return {
            "message": f"Updated {len(update.config)} configuration values",
            "keys_updated": list(update.config.keys())
        }
    else:
        raise HTTPException(500, "Failed to update configurations")


@app.delete("/config/{key:path}")
async def delete_config(key: str):
    """Delete a configuration value from Redis (falls back to env/default)."""
    if not ConfigManager:
        raise HTTPException(500, "Configuration manager not available")
    
    success = await ConfigManager.delete(key)
    
    if success:
        return {"message": f"Configuration deleted: {key}"}
    else:
        raise HTTPException(500, "Failed to delete configuration")


# =============================================================================
# Agent Health Monitoring
# =============================================================================

@app.get("/health-check", response_model=SystemHealth)
async def check_all_agents():
    """
    Check health of all registered agents.
    
    Performs parallel health checks to all agent endpoints.
    """
    agents = AgentRegistry.get_all_agents() if ConfigManager else {}
    mode = await ConfigManager.get_mode() if ConfigManager else "mock"
    
    # Parallel health checks
    tasks = []
    for agent_id, agent_info in agents.items():
        tasks.append(_check_agent_health(agent_id, agent_info))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    agent_health_list = []
    healthy_count = 0
    
    for result in results:
        if isinstance(result, AgentHealth):
            agent_health_list.append(result)
            if result.status == "healthy":
                healthy_count += 1
        elif isinstance(result, Exception):
            logger.error(f"Health check error: {result}")
    
    # Determine overall status
    total = len(agents)
    if healthy_count == total:
        overall_status = "healthy"
    elif healthy_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return SystemHealth(
        status=overall_status,
        mode=mode,
        agents=agent_health_list,
        healthy_count=healthy_count,
        total_count=total,
        timestamp=datetime.utcnow()
    )


@app.get("/health-check/{agent_id}")
async def check_single_agent(agent_id: str):
    """Check health of a specific agent."""
    agents = AgentRegistry.get_all_agents() if ConfigManager else {}
    
    if agent_id not in agents:
        raise HTTPException(404, f"Agent not found: {agent_id}")
    
    agent_info = agents[agent_id]
    result = await _check_agent_health(agent_id, agent_info)
    
    return result


async def _check_agent_health(agent_id: str, agent_info: dict) -> AgentHealth:
    """Check health of a single agent."""
    url = await ConfigManager.get(agent_info["url_key"]) if ConfigManager else None
    
    if not url:
        # Use default URL
        url = f"http://localhost:{agent_info['port']}"
    
    health_url = f"{url}{agent_info['health_path']}"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            start_time = datetime.utcnow()
            response = await client.get(health_url)
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                details = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                status = "healthy"
            else:
                details = {"error": f"HTTP {response.status_code}"}
                status = "unhealthy"
    except httpx.TimeoutException:
        status = "unhealthy"
        response_time = None
        details = {"error": "Request timeout"}
    except Exception as e:
        status = "unhealthy"
        response_time = None
        details = {"error": str(e)}
    
    HEALTH_CHECKS.labels(agent=agent_id, status=status).inc()
    
    return AgentHealth(
        agent_id=agent_id,
        name=agent_info["name"],
        url=url,
        status=status,
        response_time_ms=response_time,
        details=details,
        last_checked=datetime.utcnow()
    )


# =============================================================================
# Configuration Categories
# =============================================================================

def _get_category(key: str) -> str:
    """Determine the category for a configuration key."""
    if "jira" in key.lower():
        return "jira"
    elif "github" in key.lower():
        return "github"
    elif "jenkins" in key.lower():
        return "jenkins"
    elif "gemini" in key.lower() or "openai" in key.lower() or "llm" in key.lower():
        return "llm"
    elif "slack" in key.lower():
        return "slack"
    elif "confluence" in key.lower():
        return "confluence"
    elif "url" in key.lower():
        return "agents"
    elif "mode" in key.lower():
        return "system"
    else:
        return "other"


# =============================================================================
# Configuration Templates
# =============================================================================

@app.get("/config/templates")
async def get_config_templates():
    """Get configuration templates for different integrations."""
    return {
        "jira": {
            "name": "Jira Configuration",
            "description": "Configure Jira Cloud/Server integration",
            "fields": [
                {"key": ConfigKeys.JIRA_URL, "label": "Jira URL", "type": "url", "placeholder": "https://your-org.atlassian.net"},
                {"key": ConfigKeys.JIRA_USERNAME, "label": "Username/Email", "type": "text", "placeholder": "user@example.com"},
                {"key": ConfigKeys.JIRA_API_TOKEN, "label": "API Token", "type": "password", "placeholder": "Your Jira API token"},
                {"key": ConfigKeys.JIRA_PROJECT_KEY, "label": "Default Project", "type": "text", "placeholder": "PROJ"},
            ]
        },
        "github": {
            "name": "GitHub Configuration",
            "description": "Configure GitHub integration",
            "fields": [
                {"key": ConfigKeys.GITHUB_TOKEN, "label": "Personal Access Token", "type": "password", "placeholder": "ghp_..."},
                {"key": ConfigKeys.GITHUB_ORG, "label": "Organization", "type": "text", "placeholder": "your-org"},
                {"key": ConfigKeys.GITHUB_REPO, "label": "Default Repository", "type": "text", "placeholder": "your-repo"},
            ]
        },
        "jenkins": {
            "name": "Jenkins Configuration",
            "description": "Configure Jenkins CI integration",
            "fields": [
                {"key": ConfigKeys.JENKINS_URL, "label": "Jenkins URL", "type": "url", "placeholder": "http://jenkins:8080"},
                {"key": ConfigKeys.JENKINS_USERNAME, "label": "Username", "type": "text", "placeholder": "admin"},
                {"key": ConfigKeys.JENKINS_API_TOKEN, "label": "API Token", "type": "password", "placeholder": "Your Jenkins API token"},
            ]
        },
        "llm": {
            "name": "LLM Configuration",
            "description": "Configure AI/LLM provider",
            "fields": [
                {"key": ConfigKeys.LLM_PROVIDER, "label": "Provider", "type": "select", "options": ["google", "openai", "mock"]},
                {"key": ConfigKeys.LLM_MODEL, "label": "Model", "type": "text", "placeholder": "gemini-1.5-pro"},
                {"key": ConfigKeys.GEMINI_API_KEY, "label": "Gemini API Key", "type": "password", "placeholder": "Your Google AI API key"},
                {"key": ConfigKeys.OPENAI_API_KEY, "label": "OpenAI API Key", "type": "password", "placeholder": "sk-..."},
            ]
        },
        "slack": {
            "name": "Slack Configuration",
            "description": "Configure Slack bot integration",
            "fields": [
                {"key": ConfigKeys.SLACK_BOT_TOKEN, "label": "Bot Token", "type": "password", "placeholder": "xoxb-..."},
                {"key": ConfigKeys.SLACK_SIGNING_SECRET, "label": "Signing Secret", "type": "password", "placeholder": "Your signing secret"},
                {"key": ConfigKeys.SLACK_APP_TOKEN, "label": "App Token", "type": "password", "placeholder": "xapp-..."},
            ]
        },
        "confluence": {
            "name": "Confluence Configuration",
            "description": "Configure Confluence integration for reports",
            "fields": [
                {"key": ConfigKeys.CONFLUENCE_URL, "label": "Confluence URL", "type": "url", "placeholder": "https://your-org.atlassian.net/wiki"},
                {"key": ConfigKeys.CONFLUENCE_USERNAME, "label": "Username/Email", "type": "text", "placeholder": "user@example.com"},
                {"key": ConfigKeys.CONFLUENCE_API_TOKEN, "label": "API Token", "type": "password", "placeholder": "Your Confluence API token"},
                {"key": ConfigKeys.CONFLUENCE_SPACE_KEY, "label": "Space Key", "type": "text", "placeholder": "DOCS"},
            ]
        }
    }


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8088")),
        reload=os.getenv("ENV", "development") == "development"
    )

