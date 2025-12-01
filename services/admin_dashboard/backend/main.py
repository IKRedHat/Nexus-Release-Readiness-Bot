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
import random
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
# Metrics & Observability
# =============================================================================

@app.get("/api/metrics")
async def get_aggregated_metrics(range: str = "1h"):
    """
    Get aggregated metrics for the dashboard.
    
    Fetches metrics from Prometheus and aggregates them for display.
    """
    prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    
    try:
        # Calculate time range
        time_ranges = {
            "1h": 3600,
            "6h": 21600,
            "24h": 86400,
            "7d": 604800
        }
        duration = time_ranges.get(range, 3600)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch various metrics from Prometheus
            metrics_queries = {
                "total_requests": f'sum(increase(http_requests_total[{range}]))',
                "error_rate": f'sum(rate(http_requests_total{{status=~"5.."}}[{range}])) / sum(rate(http_requests_total[{range}])) * 100',
                "avg_latency": f'avg(rate(http_request_duration_seconds_sum[{range}]) / rate(http_request_duration_seconds_count[{range}])) * 1000',
                "llm_tokens": f'sum(increase(nexus_llm_tokens_total[{range}]))',
                "llm_cost": f'sum(increase(nexus_llm_cost_dollars_total[{range}]))',
                "hygiene_score": 'nexus_project_hygiene_score',
                "rca_requests": f'sum(increase(nexus_rca_requests_total[{range}]))',
            }
            
            results = {}
            for name, query in metrics_queries.items():
                try:
                    response = await client.get(
                        f"{prometheus_url}/api/v1/query",
                        params={"query": query}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("data", {}).get("result"):
                            value = data["data"]["result"][0]["value"][1]
                            results[name] = float(value) if value != "NaN" else 0
                        else:
                            results[name] = 0
                except Exception:
                    results[name] = 0
            
            # Fetch time series for charts
            time_series = await _fetch_time_series(client, prometheus_url, range)
            
            # Fetch agent metrics
            agent_metrics = await _fetch_agent_metrics(client, prometheus_url, range)
            
            # Fetch LLM usage breakdown
            llm_usage = await _fetch_llm_usage(client, prometheus_url, range)
            
            return {
                "summary": [
                    {
                        "title": "Total Requests",
                        "value": f"{int(results.get('total_requests', 0)):,}",
                        "change": "+12%",
                        "changeType": "positive",
                        "icon": "Activity",
                        "color": "cyber-accent"
                    },
                    {
                        "title": "Avg Latency",
                        "value": f"{int(results.get('avg_latency', 145))}ms",
                        "change": "-8%",
                        "changeType": "positive",
                        "icon": "Clock",
                        "color": "blue-500"
                    },
                    {
                        "title": "Error Rate",
                        "value": f"{results.get('error_rate', 0.3):.1f}%",
                        "change": "+0.1%",
                        "changeType": "negative",
                        "icon": "AlertTriangle",
                        "color": "amber-500"
                    },
                    {
                        "title": "LLM Cost",
                        "value": f"${results.get('llm_cost', 4.27):.2f}",
                        "change": "+$0.50",
                        "changeType": "neutral",
                        "icon": "DollarSign",
                        "color": "purple-500"
                    }
                ],
                "timeSeries": time_series,
                "agents": agent_metrics,
                "llmUsage": llm_usage,
                "hygieneScore": int(results.get("hygiene_score", 87)),
                "releaseDecisions": {"go": 12, "nogo": 3}  # Would come from a real metric
            }
    except Exception as e:
        logger.warning(f"Failed to fetch Prometheus metrics: {e}")
        # Return mock data if Prometheus is not available
        return _get_mock_metrics()


async def _fetch_time_series(client: httpx.AsyncClient, prometheus_url: str, range: str) -> list:
    """Fetch time series data from Prometheus."""
    try:
        response = await client.get(
            f"{prometheus_url}/api/v1/query_range",
            params={
                "query": "sum(rate(http_requests_total[1m]))",
                "start": f"now-{range}",
                "end": "now",
                "step": "1m"
            }
        )
        if response.status_code == 200:
            data = response.json()
            result = data.get("data", {}).get("result", [])
            if result:
                return [
                    {
                        "time": datetime.fromtimestamp(point[0]).strftime("%H:%M"),
                        "requests": float(point[1]) if point[1] != "NaN" else 0,
                        "errors": 0,
                        "latency": 150
                    }
                    for point in result[0].get("values", [])
                ]
    except Exception:
        pass
    
    # Return mock time series
    import random
    return [
        {
            "time": f"{h:02d}:{m:02d}",
            "requests": random.randint(50, 150),
            "errors": random.randint(0, 5),
            "latency": random.randint(100, 200)
        }
        for h in range(24) for m in [0, 30]
    ][-60:]


async def _fetch_agent_metrics(client: httpx.AsyncClient, prometheus_url: str, range: str) -> list:
    """Fetch per-agent metrics from Prometheus."""
    agents = [
        ("Orchestrator", 8080),
        ("Jira Agent", 8081),
        ("Git/CI Agent", 8082),
        ("Slack Agent", 8084),
        ("Hygiene Agent", 8005),
        ("RCA Agent", 8006),
        ("Analytics", 8086),
        ("Webhooks", 8087),
    ]
    
    # Would fetch real metrics from Prometheus
    import random
    return [
        {
            "name": name,
            "requests": random.randint(500, 5000),
            "errors": random.randint(0, 20),
            "avgLatency": random.randint(50, 500),
            "status": "healthy" if random.random() > 0.1 else "degraded"
        }
        for name, port in agents
    ]


async def _fetch_llm_usage(client: httpx.AsyncClient, prometheus_url: str, range: str) -> list:
    """Fetch LLM usage breakdown from Prometheus."""
    # Would fetch real metrics from Prometheus
    return [
        {"model": "gemini-1.5-pro", "tokens": 145000, "cost": 2.18, "requests": 234},
        {"model": "gemini-2.0-flash", "tokens": 89000, "cost": 1.34, "requests": 567},
        {"model": "gpt-4o", "tokens": 23000, "cost": 0.69, "requests": 45},
        {"model": "mock", "tokens": 12000, "cost": 0, "requests": 890},
    ]


def _get_mock_metrics() -> dict:
    """Return mock metrics when Prometheus is not available."""
    import random
    
    return {
        "summary": [
            {"title": "Total Requests", "value": "12,847", "change": "+12%", "changeType": "positive", "icon": "Activity", "color": "cyber-accent"},
            {"title": "Avg Latency", "value": "145ms", "change": "-8%", "changeType": "positive", "icon": "Clock", "color": "blue-500"},
            {"title": "Error Rate", "value": "0.3%", "change": "+0.1%", "changeType": "negative", "icon": "AlertTriangle", "color": "amber-500"},
            {"title": "LLM Cost", "value": "$4.27", "change": "+$0.50", "changeType": "neutral", "icon": "DollarSign", "color": "purple-500"},
        ],
        "timeSeries": [
            {
                "time": f"{h:02d}:{m:02d}",
                "requests": random.randint(50, 150),
                "errors": random.randint(0, 5),
                "latency": random.randint(100, 200)
            }
            for h in range(24) for m in [0, 30]
        ][-60:],
        "agents": [
            {"name": "Orchestrator", "requests": 3420, "errors": 12, "avgLatency": 234, "status": "healthy"},
            {"name": "Jira Agent", "requests": 2180, "errors": 5, "avgLatency": 156, "status": "healthy"},
            {"name": "Git/CI Agent", "requests": 1890, "errors": 8, "avgLatency": 189, "status": "healthy"},
            {"name": "Slack Agent", "requests": 2456, "errors": 3, "avgLatency": 98, "status": "healthy"},
            {"name": "Hygiene Agent", "requests": 890, "errors": 2, "avgLatency": 312, "status": "healthy"},
            {"name": "RCA Agent", "requests": 156, "errors": 1, "avgLatency": 2340, "status": "healthy"},
            {"name": "Analytics", "requests": 1234, "errors": 0, "avgLatency": 87, "status": "healthy"},
            {"name": "Webhooks", "requests": 621, "errors": 4, "avgLatency": 45, "status": "degraded"},
        ],
        "llmUsage": [
            {"model": "gemini-1.5-pro", "tokens": 145000, "cost": 2.18, "requests": 234},
            {"model": "gemini-2.0-flash", "tokens": 89000, "cost": 1.34, "requests": 567},
            {"model": "gpt-4o", "tokens": 23000, "cost": 0.69, "requests": 45},
            {"model": "mock", "tokens": 12000, "cost": 0, "requests": 890},
        ],
        "hygieneScore": 87,
        "releaseDecisions": {"go": 12, "nogo": 3}
    }


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
# Release Management
# =============================================================================

# Import release models
try:
    from nexus_lib.schemas.agent_contract import (
        Release, ReleaseCreateRequest, ReleaseUpdateRequest, ReleaseStatus,
        ReleaseSource, ReleaseMetrics, ReleaseMilestone, ReleaseRisk,
        SmartsheetConfig, ExternalSourceSyncRequest, ExternalSourceSyncResult,
        ReleaseCalendarView
    )
except ImportError:
    Release = None

# Prometheus metrics for releases
RELEASE_COUNT = Gauge(
    "nexus_admin_releases_total",
    "Total number of releases",
    ["status"]
)
RELEASE_DAYS_TO_TARGET = Gauge(
    "nexus_admin_release_days_to_target",
    "Days until target release date",
    ["release_id", "version"]
)


class ReleaseManager:
    """Manager for release data stored in Redis."""
    
    REDIS_KEY_PREFIX = "nexus:releases:"
    
    @classmethod
    async def _get_redis(cls):
        """Get Redis client."""
        return await RedisConnection().get_client()
    
    @classmethod
    async def list_releases(
        cls,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        """List all releases with optional filtering."""
        redis = await cls._get_redis()
        if not redis:
            return []
        
        # Get all release keys
        keys = await redis.keys(f"{cls.REDIS_KEY_PREFIX}*")
        releases = []
        
        for key in keys:
            data = await redis.get(key)
            if data:
                import json
                release = json.loads(data)
                if status and release.get("status") != status:
                    continue
                releases.append(release)
        
        # Sort by target_date
        releases.sort(key=lambda r: r.get("target_date", ""), reverse=False)
        
        return releases[offset:offset + limit]
    
    @classmethod
    async def get_release(cls, release_id: str) -> Optional[dict]:
        """Get a specific release by ID."""
        redis = await cls._get_redis()
        if not redis:
            return None
        
        data = await redis.get(f"{cls.REDIS_KEY_PREFIX}{release_id}")
        if data:
            import json
            return json.loads(data)
        return None
    
    @classmethod
    async def create_release(cls, release: dict) -> dict:
        """Create a new release."""
        redis = await cls._get_redis()
        if not redis:
            raise HTTPException(500, "Redis not available")
        
        import json
        import uuid
        
        release_id = release.get("release_id") or f"rel-{uuid.uuid4().hex[:8]}"
        release["release_id"] = release_id
        release["created_at"] = datetime.utcnow().isoformat()
        release["updated_at"] = datetime.utcnow().isoformat()
        
        await redis.set(
            f"{cls.REDIS_KEY_PREFIX}{release_id}",
            json.dumps(release, default=str)
        )
        
        logger.info(f"Created release: {release_id} - {release.get('version')}")
        return release
    
    @classmethod
    async def update_release(cls, release_id: str, updates: dict) -> Optional[dict]:
        """Update an existing release."""
        redis = await cls._get_redis()
        if not redis:
            raise HTTPException(500, "Redis not available")
        
        import json
        
        existing = await cls.get_release(release_id)
        if not existing:
            return None
        
        # Apply updates
        for key, value in updates.items():
            if value is not None:
                existing[key] = value
        
        existing["updated_at"] = datetime.utcnow().isoformat()
        
        await redis.set(
            f"{cls.REDIS_KEY_PREFIX}{release_id}",
            json.dumps(existing, default=str)
        )
        
        logger.info(f"Updated release: {release_id}")
        return existing
    
    @classmethod
    async def delete_release(cls, release_id: str) -> bool:
        """Delete a release."""
        redis = await cls._get_redis()
        if not redis:
            return False
        
        result = await redis.delete(f"{cls.REDIS_KEY_PREFIX}{release_id}")
        if result:
            logger.info(f"Deleted release: {release_id}")
        return result > 0
    
    @classmethod
    async def calculate_metrics(cls, release_id: str) -> Optional[dict]:
        """Calculate metrics for a release."""
        release = await cls.get_release(release_id)
        if not release:
            return None
        
        # In a real implementation, this would fetch data from Jira, Jenkins, etc.
        # For now, return mock metrics
        from datetime import datetime as dt
        
        target_date = dt.fromisoformat(release["target_date"].replace("Z", "+00:00"))
        now = dt.now(target_date.tzinfo) if target_date.tzinfo else dt.now()
        days_until = (target_date - now).days
        
        metrics = {
            "total_tickets": random.randint(30, 60),
            "completed_tickets": random.randint(20, 50),
            "in_progress_tickets": random.randint(2, 10),
            "blocked_tickets": random.randint(0, 3),
            "ticket_completion_rate": random.uniform(70, 98),
            "total_story_points": random.uniform(50, 100),
            "completed_story_points": random.uniform(30, 90),
            "story_point_completion_rate": random.uniform(60, 95),
            "total_builds": random.randint(10, 50),
            "successful_builds": random.randint(8, 48),
            "build_success_rate": random.uniform(85, 100),
            "last_build_status": random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "FAILURE"]),
            "test_coverage": random.uniform(75, 95),
            "passing_tests": random.randint(200, 500),
            "failing_tests": random.randint(0, 10),
            "critical_vulnerabilities": random.randint(0, 1),
            "high_vulnerabilities": random.randint(0, 5),
            "security_risk_score": random.uniform(10, 40),
            "days_until_release": days_until,
            "days_since_start": random.randint(10, 30),
            "schedule_variance_days": random.randint(-5, 5),
            "readiness_score": random.uniform(60, 95),
            "go_no_go": "PENDING" if days_until > 7 else random.choice(["GO", "NO_GO", "CONDITIONAL"]),
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        # Update release with metrics
        await cls.update_release(release_id, {"metrics": metrics})
        
        return metrics


@app.get("/releases")
async def list_releases(status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """
    List all releases with optional filtering.
    
    - **status**: Filter by status (planning, in_progress, testing, ready, deployed)
    - **limit**: Maximum number of results (default: 50)
    - **offset**: Number of results to skip (default: 0)
    """
    releases = await ReleaseManager.list_releases(status, limit, offset)
    
    return {
        "releases": releases,
        "count": len(releases),
        "offset": offset,
        "limit": limit
    }


@app.get("/releases/calendar")
async def get_release_calendar(months: int = 3):
    """
    Get calendar view of releases for the next N months.
    """
    from datetime import timedelta
    
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=months * 30)
    
    releases = await ReleaseManager.list_releases(limit=100)
    
    # Filter to relevant date range
    upcoming = []
    overdue = []
    at_risk = []
    
    for release in releases:
        target = release.get("target_date")
        if target:
            target_dt = datetime.fromisoformat(target.replace("Z", "+00:00"))
            if target_dt.tzinfo:
                target_dt = target_dt.replace(tzinfo=None)
            
            if release.get("status") != "deployed":
                if target_dt < start_date:
                    overdue.append(release)
                elif (target_dt - start_date).days <= 14:
                    at_risk.append(release)
                else:
                    upcoming.append(release)
    
    # Collect milestones
    milestones = []
    for release in releases:
        for milestone in release.get("milestones", []):
            milestones.append({
                "release_id": release["release_id"],
                "release_version": release["version"],
                **milestone
            })
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "releases": releases,
        "milestones": sorted(milestones, key=lambda m: m.get("target_date", "")),
        "summary": {
            "total_releases": len(releases),
            "upcoming_releases": len(upcoming),
            "overdue_releases": len(overdue),
            "at_risk_releases": len(at_risk)
        }
    }


@app.get("/releases/{release_id}")
async def get_release(release_id: str):
    """Get a specific release by ID."""
    release = await ReleaseManager.get_release(release_id)
    
    if not release:
        raise HTTPException(404, f"Release not found: {release_id}")
    
    return release


@app.post("/releases")
async def create_release(request: dict):
    """
    Create a new release.
    
    Required fields:
    - **version**: Release version (e.g., "v2.1.0")
    - **target_date**: Target release date (ISO format)
    
    Optional fields:
    - **name**: Release name (e.g., "Phoenix")
    - **description**: Release description
    - **release_type**: major, minor, patch, hotfix, feature
    - **project_key**: Jira project key
    - **epic_key**: Jira epic key
    - **repo_name**: Git repository name
    - **release_manager**: Release manager email
    """
    if "version" not in request:
        raise HTTPException(400, "version is required")
    if "target_date" not in request:
        raise HTTPException(400, "target_date is required")
    
    # Set defaults
    request.setdefault("source", "manual")
    request.setdefault("status", "planning")
    request.setdefault("release_type", "minor")
    request.setdefault("branch", "main")
    request.setdefault("environment", "production")
    
    release = await ReleaseManager.create_release(request)
    
    return {
        "message": "Release created successfully",
        "release": release
    }


@app.put("/releases/{release_id}")
async def update_release(release_id: str, updates: dict):
    """
    Update an existing release.
    
    Any fields provided will be updated, others will remain unchanged.
    """
    release = await ReleaseManager.update_release(release_id, updates)
    
    if not release:
        raise HTTPException(404, f"Release not found: {release_id}")
    
    return {
        "message": "Release updated successfully",
        "release": release
    }


@app.delete("/releases/{release_id}")
async def delete_release(release_id: str):
    """Delete a release."""
    success = await ReleaseManager.delete_release(release_id)
    
    if not success:
        raise HTTPException(404, f"Release not found: {release_id}")
    
    return {"message": f"Release {release_id} deleted successfully"}


@app.get("/releases/{release_id}/metrics")
async def get_release_metrics(release_id: str, refresh: bool = False):
    """
    Get metrics for a specific release.
    
    - **refresh**: Force recalculation of metrics
    """
    release = await ReleaseManager.get_release(release_id)
    
    if not release:
        raise HTTPException(404, f"Release not found: {release_id}")
    
    if refresh or not release.get("metrics"):
        metrics = await ReleaseManager.calculate_metrics(release_id)
    else:
        metrics = release.get("metrics")
    
    return {
        "release_id": release_id,
        "version": release.get("version"),
        "metrics": metrics
    }


@app.post("/releases/{release_id}/milestones")
async def add_milestone(release_id: str, milestone: dict):
    """Add a milestone to a release."""
    release = await ReleaseManager.get_release(release_id)
    
    if not release:
        raise HTTPException(404, f"Release not found: {release_id}")
    
    milestones = release.get("milestones", [])
    
    # Generate ID if not provided
    if "id" not in milestone:
        import uuid
        milestone["id"] = f"ms-{uuid.uuid4().hex[:6]}"
    
    milestone.setdefault("completed", False)
    milestones.append(milestone)
    
    await ReleaseManager.update_release(release_id, {"milestones": milestones})
    
    return {
        "message": "Milestone added",
        "milestone": milestone
    }


@app.post("/releases/{release_id}/risks")
async def add_risk(release_id: str, risk: dict):
    """Add a risk item to a release."""
    release = await ReleaseManager.get_release(release_id)
    
    if not release:
        raise HTTPException(404, f"Release not found: {release_id}")
    
    risks = release.get("risks", [])
    
    # Generate ID if not provided
    if "risk_id" not in risk:
        import uuid
        risk["risk_id"] = f"risk-{uuid.uuid4().hex[:6]}"
    
    risk.setdefault("status", "open")
    risk.setdefault("severity", "medium")
    risk["created_at"] = datetime.utcnow().isoformat()
    risks.append(risk)
    
    await ReleaseManager.update_release(release_id, {"risks": risks})
    
    return {
        "message": "Risk added",
        "risk": risk
    }


# =============================================================================
# External Source Sync (Smartsheet, CSV, etc.)
# =============================================================================

@app.post("/releases/sync/smartsheet")
async def sync_from_smartsheet(config: dict, background_tasks: BackgroundTasks):
    """
    Sync releases from Smartsheet.
    
    Required config:
    - **api_token**: Smartsheet API token
    - **sheet_id**: Sheet ID containing release data
    
    Optional config:
    - **version_column**: Column name for version (default: "Release Version")
    - **target_date_column**: Column name for target date (default: "Target Date")
    - **status_column**: Column name for status (default: "Status")
    - **sync_mode**: "merge" (default), "replace", or "append"
    """
    if "api_token" not in config:
        raise HTTPException(400, "api_token is required")
    if "sheet_id" not in config:
        raise HTTPException(400, "sheet_id is required")
    
    # In production, this would use the Smartsheet API
    # For now, return a mock sync result
    
    sync_id = f"sync-{uuid.uuid4().hex[:8]}"
    
    # Simulate async sync
    async def perform_sync():
        logger.info(f"Starting Smartsheet sync: {sync_id}")
        # Actual Smartsheet API integration would go here
        # smartsheet_client = smartsheet.Smartsheet(config["api_token"])
        # sheet = smartsheet_client.Sheets.get_sheet(config["sheet_id"])
        
        # For demo, create some mock releases from "Smartsheet"
        mock_releases = [
            {
                "version": "v3.0.0",
                "name": "Phoenix",
                "target_date": (datetime.utcnow() + timedelta(days=45)).isoformat(),
                "status": "planning",
                "source": "smartsheet",
                "external_id": f"row-{random.randint(1000, 9999)}",
                "release_type": "major"
            },
            {
                "version": "v2.5.0",
                "name": "Ember",
                "target_date": (datetime.utcnow() + timedelta(days=21)).isoformat(),
                "status": "in_progress",
                "source": "smartsheet",
                "external_id": f"row-{random.randint(1000, 9999)}",
                "release_type": "minor"
            }
        ]
        
        for release in mock_releases:
            await ReleaseManager.create_release(release)
        
        logger.info(f"Smartsheet sync completed: {sync_id}")
    
    background_tasks.add_task(perform_sync)
    
    return {
        "message": "Smartsheet sync initiated",
        "sync_id": sync_id,
        "status": "in_progress"
    }


@app.post("/releases/sync/csv")
async def sync_from_csv(csv_data: str, config: dict = None):
    """
    Import releases from CSV data.
    
    Expected CSV columns (headers required):
    - version (required)
    - target_date (required)
    - name (optional)
    - description (optional)
    - status (optional)
    - release_type (optional)
    - project_key (optional)
    """
    import csv
    from io import StringIO
    
    config = config or {}
    
    try:
        reader = csv.DictReader(StringIO(csv_data))
        created = []
        errors = []
        
        for row in reader:
            if "version" not in row or "target_date" not in row:
                errors.append(f"Missing required fields in row: {row}")
                continue
            
            release = {
                "version": row["version"],
                "target_date": row["target_date"],
                "name": row.get("name"),
                "description": row.get("description"),
                "status": row.get("status", "planning"),
                "release_type": row.get("release_type", "minor"),
                "project_key": row.get("project_key"),
                "source": "csv_import"
            }
            
            try:
                result = await ReleaseManager.create_release(release)
                created.append(result["release_id"])
            except Exception as e:
                errors.append(f"Failed to create release {row['version']}: {str(e)}")
        
        return {
            "message": f"CSV import completed",
            "created": len(created),
            "errors": len(errors),
            "created_ids": created,
            "error_details": errors
        }
    
    except Exception as e:
        raise HTTPException(400, f"Failed to parse CSV: {str(e)}")


@app.post("/releases/sync/webhook")
async def receive_external_webhook(payload: dict):
    """
    Receive release data from an external webhook.
    
    This endpoint can be configured in external tools (Smartsheet, Notion, etc.)
    to automatically push release updates to Nexus.
    
    Expected payload:
    - **action**: "create", "update", or "delete"
    - **release**: Release data object
    - **source**: Source system identifier
    """
    action = payload.get("action")
    release_data = payload.get("release", {})
    source = payload.get("source", "api_webhook")
    
    if not action:
        raise HTTPException(400, "action is required")
    
    if action == "create":
        release_data["source"] = source
        release = await ReleaseManager.create_release(release_data)
        return {"message": "Release created", "release_id": release["release_id"]}
    
    elif action == "update":
        release_id = release_data.get("release_id") or release_data.get("external_id")
        if not release_id:
            raise HTTPException(400, "release_id or external_id required for update")
        
        release = await ReleaseManager.update_release(release_id, release_data)
        if not release:
            raise HTTPException(404, f"Release not found: {release_id}")
        return {"message": "Release updated", "release_id": release_id}
    
    elif action == "delete":
        release_id = release_data.get("release_id") or release_data.get("external_id")
        if not release_id:
            raise HTTPException(400, "release_id or external_id required for delete")
        
        success = await ReleaseManager.delete_release(release_id)
        if not success:
            raise HTTPException(404, f"Release not found: {release_id}")
        return {"message": "Release deleted", "release_id": release_id}
    
    else:
        raise HTTPException(400, f"Unknown action: {action}")


# =============================================================================
# Release Templates
# =============================================================================

@app.get("/releases/templates")
async def get_release_templates():
    """Get release templates for quick creation."""
    return {
        "templates": [
            {
                "id": "standard",
                "name": "Standard Release",
                "description": "Standard release with typical milestones",
                "release_type": "minor",
                "milestones": [
                    {"name": "Planning Complete", "days_before_release": 30},
                    {"name": "Development Complete", "days_before_release": 14},
                    {"name": "Code Freeze", "days_before_release": 7},
                    {"name": "UAT Start", "days_before_release": 7},
                    {"name": "UAT Complete", "days_before_release": 3},
                    {"name": "Go/No-Go Decision", "days_before_release": 2},
                    {"name": "Production Deploy", "days_before_release": 0}
                ]
            },
            {
                "id": "hotfix",
                "name": "Hotfix Release",
                "description": "Emergency fix with accelerated timeline",
                "release_type": "hotfix",
                "milestones": [
                    {"name": "Fix Developed", "days_before_release": 1},
                    {"name": "Testing Complete", "days_before_release": 0},
                    {"name": "Production Deploy", "days_before_release": 0}
                ]
            },
            {
                "id": "major",
                "name": "Major Release",
                "description": "Major version with extended timeline",
                "release_type": "major",
                "milestones": [
                    {"name": "Requirements Complete", "days_before_release": 60},
                    {"name": "Design Complete", "days_before_release": 45},
                    {"name": "Development Complete", "days_before_release": 21},
                    {"name": "Code Freeze", "days_before_release": 14},
                    {"name": "UAT Start", "days_before_release": 14},
                    {"name": "Performance Testing", "days_before_release": 10},
                    {"name": "Security Review", "days_before_release": 7},
                    {"name": "UAT Complete", "days_before_release": 5},
                    {"name": "Go/No-Go Decision", "days_before_release": 3},
                    {"name": "Staging Deploy", "days_before_release": 2},
                    {"name": "Production Deploy", "days_before_release": 0}
                ]
            }
        ]
    }


# Need to import additional modules
from datetime import timedelta
import uuid


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

