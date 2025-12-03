"""
Nexus Specialist Registry
Production-ready agent registration, discovery, and health management
"""
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

import httpx

logger = logging.getLogger("nexus.specialists")


# =============================================================================
# ENUMS AND MODELS
# =============================================================================

class SpecialistStatus(str, Enum):
    """Health status of a specialist agent"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class SpecialistCategory(str, Enum):
    """Category of specialist agent"""
    CORE = "core"           # Essential for basic operations
    DATA = "data"           # Data source integrations
    COMMUNICATION = "comm"  # User-facing communication
    ANALYSIS = "analysis"   # Analysis and reporting
    AUTOMATION = "auto"     # Automation and scheduling
    OBSERVABILITY = "obs"   # Metrics and monitoring


class ToolParameter(BaseModel):
    """Parameter definition for a specialist tool"""
    name: str
    type: str = "string"
    description: str
    required: bool = False
    default: Optional[Any] = None


class SpecialistTool(BaseModel):
    """Tool/capability provided by a specialist"""
    name: str
    description: str
    endpoint: str
    method: str = "GET"
    parameters: List[ToolParameter] = Field(default_factory=list)
    
    @property
    def required_params(self) -> List[str]:
        return [p.name for p in self.parameters if p.required]


class SpecialistDefinition(BaseModel):
    """Complete definition of a specialist agent"""
    id: str
    name: str
    description: str
    category: SpecialistCategory
    port: int
    health_path: str = "/health"
    env_url_key: str
    tools: List[SpecialistTool] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)  # IDs of dependent specialists
    is_critical: bool = False  # If True, Orchestrator won't start without it


@dataclass
class SpecialistHealth:
    """Runtime health information for a specialist"""
    status: SpecialistStatus = SpecialistStatus.UNKNOWN
    last_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SPECIALIST DEFINITIONS
# =============================================================================

# Define all specialist agents with their capabilities
SPECIALIST_DEFINITIONS: Dict[str, SpecialistDefinition] = {
    # --- CORE AGENTS ---
    "jira": SpecialistDefinition(
        id="jira",
        name="Jira Agent",
        description="Manages Jira operations including ticket CRUD, search, sprint statistics, and hierarchy traversal.",
        category=SpecialistCategory.DATA,
        port=8081,
        env_url_key="JIRA_AGENT_URL",
        is_critical=True,
        tools=[
            SpecialistTool(
                name="get_jira_ticket",
                description="Fetch details of a Jira ticket by its key (e.g., PROJ-123). Returns ticket summary, status, assignee, and other details.",
                endpoint="/issue/{ticket_key}",
                method="GET",
                parameters=[ToolParameter(name="ticket_key", description="Jira ticket key", required=True)]
            ),
            SpecialistTool(
                name="get_ticket_hierarchy",
                description="Fetch the complete hierarchy of tickets under an Epic. Shows Epic -> Stories -> Subtasks structure.",
                endpoint="/hierarchy/{ticket_key}",
                method="GET",
                parameters=[ToolParameter(name="ticket_key", description="Epic ticket key", required=True)]
            ),
            SpecialistTool(
                name="search_jira",
                description="Search Jira tickets using JQL (Jira Query Language). Example: 'project = PROJ AND status = \"In Progress\"'",
                endpoint="/search",
                method="GET",
                parameters=[ToolParameter(name="jql", description="JQL query string", required=True)]
            ),
            SpecialistTool(
                name="update_jira_ticket",
                description="Update a Jira ticket's status or add a comment. Requires ticket key and either status or comment.",
                endpoint="/update",
                method="POST",
                parameters=[
                    ToolParameter(name="key", description="Ticket key", required=True),
                    ToolParameter(name="status", description="New status"),
                    ToolParameter(name="comment", description="Comment text")
                ]
            ),
            SpecialistTool(
                name="get_sprint_stats",
                description="Get sprint statistics including completion rate, story points, and blockers for a project.",
                endpoint="/sprint-stats/{project_key}",
                method="GET",
                parameters=[ToolParameter(name="project_key", description="Jira project key", required=True)]
            ),
        ]
    ),
    
    "git_ci": SpecialistDefinition(
        id="git_ci",
        name="Git/CI Agent",
        description="Manages GitHub and Jenkins operations including repository health, PRs, builds, and security scans.",
        category=SpecialistCategory.DATA,
        port=8082,
        env_url_key="GIT_CI_AGENT_URL",
        is_critical=True,
        tools=[
            SpecialistTool(
                name="get_repo_health",
                description="Check GitHub repository health including branch status, open PRs, and CI status.",
                endpoint="/repo/{repo_name}/health",
                method="GET",
                parameters=[ToolParameter(name="repo_name", description="Repository name (org/repo)", required=True)]
            ),
            SpecialistTool(
                name="get_pr_status",
                description="Get details of a specific GitHub Pull Request including CI status and approvals.",
                endpoint="/repo/{repo_name}/pr/{pr_number}",
                method="GET",
                parameters=[
                    ToolParameter(name="repo_name", description="Repository name", required=True),
                    ToolParameter(name="pr_number", description="PR number", required=True)
                ]
            ),
            SpecialistTool(
                name="get_build_status",
                description="Get Jenkins build status for a job. Returns build result, test results, and artifacts.",
                endpoint="/build/{job_name}/status",
                method="GET",
                parameters=[ToolParameter(name="job_name", description="Jenkins job name", required=True)]
            ),
            SpecialistTool(
                name="trigger_build",
                description="Trigger a new Jenkins build for a specified job.",
                endpoint="/build/{job_name}",
                method="POST",
                parameters=[ToolParameter(name="job_name", description="Jenkins job name", required=True)]
            ),
            SpecialistTool(
                name="get_security_scan",
                description="Get security scan results for a repository including vulnerabilities and risk score.",
                endpoint="/security/{repo_name}",
                method="GET",
                parameters=[ToolParameter(name="repo_name", description="Repository name", required=True)]
            ),
        ]
    ),
    
    "slack": SpecialistDefinition(
        id="slack",
        name="Slack Agent",
        description="Handles Slack integrations including notifications, interactive messages, and slash commands.",
        category=SpecialistCategory.COMMUNICATION,
        port=8084,
        env_url_key="SLACK_AGENT_URL",
        is_critical=False,
        tools=[
            SpecialistTool(
                name="send_slack_notification",
                description="Send a message to a Slack channel with optional Block Kit formatting.",
                endpoint="/notify",
                method="POST",
                parameters=[
                    ToolParameter(name="channel", description="Channel ID or name", required=True),
                    ToolParameter(name="message", description="Message text", required=True),
                    ToolParameter(name="blocks", description="Block Kit blocks (optional)")
                ]
            ),
            SpecialistTool(
                name="send_slack_dm",
                description="Send a direct message to a Slack user.",
                endpoint="/dm",
                method="POST",
                parameters=[
                    ToolParameter(name="user_id", description="Slack user ID", required=True),
                    ToolParameter(name="message", description="Message text", required=True)
                ]
            ),
        ]
    ),
    
    "reporting": SpecialistDefinition(
        id="reporting",
        name="Reporting Agent",
        description="Generates and publishes release readiness reports to various destinations including Confluence.",
        category=SpecialistCategory.ANALYSIS,
        port=8083,
        env_url_key="REPORTING_AGENT_URL",
        is_critical=True,
        dependencies=["jira", "git_ci"],
        tools=[
            SpecialistTool(
                name="generate_report",
                description="Generate a release readiness HTML report from provided data.",
                endpoint="/generate",
                method="POST",
                parameters=[ToolParameter(name="report_data", description="Report data object", required=True)]
            ),
            SpecialistTool(
                name="publish_report",
                description="Publish a report to Confluence. Can create a new page or update existing.",
                endpoint="/publish",
                method="POST",
                parameters=[
                    ToolParameter(name="title", description="Page title", required=True),
                    ToolParameter(name="report_data", description="Report data", required=True),
                    ToolParameter(name="page_id", description="Existing page ID (optional)"),
                    ToolParameter(name="space_key", description="Confluence space")
                ]
            ),
            SpecialistTool(
                name="analyze_readiness",
                description="Analyze release data and determine Go/No-Go decision with checklist.",
                endpoint="/analyze",
                method="POST",
                parameters=[ToolParameter(name="report_data", description="Report data", required=True)]
            ),
        ]
    ),
    
    # --- PROACTIVE QUALITY AGENTS ---
    "hygiene": SpecialistDefinition(
        id="hygiene",
        name="Jira Hygiene Agent",
        description="Proactively monitors Jira data quality, identifies issues, and can auto-fix common problems.",
        category=SpecialistCategory.AUTOMATION,
        port=8005,
        env_url_key="HYGIENE_AGENT_URL",
        is_critical=False,
        dependencies=["jira", "slack"],
        tools=[
            SpecialistTool(
                name="run_hygiene_check",
                description="Run a hygiene check on Jira data for a project. Identifies missing fields, stale tickets, and other quality issues.",
                endpoint="/check/{project_key}",
                method="POST",
                parameters=[
                    ToolParameter(name="project_key", description="Jira project key", required=True),
                    ToolParameter(name="check_types", description="Types of checks to run (optional, defaults to all)")
                ]
            ),
            SpecialistTool(
                name="get_hygiene_score",
                description="Get the current hygiene score for a project. Returns score, trends, and issue breakdown.",
                endpoint="/score/{project_key}",
                method="GET",
                parameters=[ToolParameter(name="project_key", description="Jira project key", required=True)]
            ),
            SpecialistTool(
                name="fix_hygiene_issues",
                description="Automatically fix identified hygiene issues for a project.",
                endpoint="/fix",
                method="POST",
                parameters=[
                    ToolParameter(name="project_key", description="Jira project key", required=True),
                    ToolParameter(name="issue_ids", description="Specific issue IDs to fix (optional)")
                ]
            ),
            SpecialistTool(
                name="get_hygiene_history",
                description="Get historical hygiene scores and trends for a project.",
                endpoint="/history/{project_key}",
                method="GET",
                parameters=[ToolParameter(name="project_key", description="Jira project key", required=True)]
            ),
        ]
    ),
    
    "rca": SpecialistDefinition(
        id="rca",
        name="RCA Agent",
        description="Root Cause Analysis agent that diagnoses build failures by correlating logs with code changes.",
        category=SpecialistCategory.ANALYSIS,
        port=8006,
        env_url_key="RCA_AGENT_URL",
        is_critical=False,
        dependencies=["git_ci"],
        tools=[
            SpecialistTool(
                name="analyze_build_failure",
                description="Analyze a failed Jenkins build to determine root cause. Uses LLM to correlate error logs with git diffs to identify which code change caused the failure and suggest fixes.",
                endpoint="/analyze",
                method="POST",
                parameters=[
                    ToolParameter(name="job_name", description="Jenkins job name", required=True),
                    ToolParameter(name="build_number", description="Build number to analyze", required=True),
                    ToolParameter(name="repo_name", description="GitHub repository name"),
                    ToolParameter(name="pr_id", description="Pull request ID"),
                    ToolParameter(name="commit_sha", description="Specific commit SHA")
                ]
            ),
            SpecialistTool(
                name="get_rca_history",
                description="Get history of RCA analyses for a job or repository.",
                endpoint="/history",
                method="GET",
                parameters=[
                    ToolParameter(name="job_name", description="Jenkins job name"),
                    ToolParameter(name="repo_name", description="Repository name")
                ]
            ),
        ]
    ),
    
    # --- ANALYTICS AND OBSERVABILITY ---
    "analytics": SpecialistDefinition(
        id="analytics",
        name="Analytics Service",
        description="Provides DORA metrics, KPIs, trend analysis, and predictive insights for release management.",
        category=SpecialistCategory.OBSERVABILITY,
        port=8086,
        env_url_key="ANALYTICS_URL",
        is_critical=False,
        tools=[
            SpecialistTool(
                name="get_dora_metrics",
                description="Get DORA (DevOps Research and Assessment) metrics: deployment frequency, lead time, change failure rate, and MTTR.",
                endpoint="/dora",
                method="GET",
                parameters=[
                    ToolParameter(name="project", description="Project identifier"),
                    ToolParameter(name="from_date", description="Start date (ISO format)"),
                    ToolParameter(name="to_date", description="End date (ISO format)")
                ]
            ),
            SpecialistTool(
                name="get_release_kpis",
                description="Get key performance indicators for releases including velocity, quality, and efficiency metrics.",
                endpoint="/kpis",
                method="GET",
                parameters=[
                    ToolParameter(name="project", description="Project identifier"),
                    ToolParameter(name="release_version", description="Specific release version")
                ]
            ),
            SpecialistTool(
                name="get_trend_analysis",
                description="Analyze trends in release metrics over time. Identifies patterns, anomalies, and forecasts.",
                endpoint="/trends",
                method="GET",
                parameters=[
                    ToolParameter(name="metric", description="Metric to analyze (e.g., velocity, quality)"),
                    ToolParameter(name="period", description="Time period (7d, 30d, 90d)")
                ]
            ),
            SpecialistTool(
                name="predict_release_readiness",
                description="Predict release readiness based on historical data and current trajectory.",
                endpoint="/predict",
                method="POST",
                parameters=[
                    ToolParameter(name="release_version", description="Release version to predict", required=True),
                    ToolParameter(name="target_date", description="Target release date")
                ]
            ),
        ]
    ),
    
    "webhooks": SpecialistDefinition(
        id="webhooks",
        name="Webhooks Service",
        description="Manages webhook subscriptions for external event notifications and integrations.",
        category=SpecialistCategory.AUTOMATION,
        port=8087,
        env_url_key="WEBHOOKS_URL",
        is_critical=False,
        tools=[
            SpecialistTool(
                name="create_webhook_subscription",
                description="Create a new webhook subscription for event notifications.",
                endpoint="/subscriptions",
                method="POST",
                parameters=[
                    ToolParameter(name="event_type", description="Event type to subscribe to", required=True),
                    ToolParameter(name="target_url", description="URL to receive webhooks", required=True),
                    ToolParameter(name="secret", description="HMAC secret for signature verification")
                ]
            ),
            SpecialistTool(
                name="list_webhook_subscriptions",
                description="List all active webhook subscriptions.",
                endpoint="/subscriptions",
                method="GET",
                parameters=[]
            ),
            SpecialistTool(
                name="get_webhook_delivery_status",
                description="Get delivery status and history for webhook events.",
                endpoint="/deliveries",
                method="GET",
                parameters=[ToolParameter(name="subscription_id", description="Subscription ID")]
            ),
        ]
    ),
    
    # --- SCHEDULING ---
    "scheduling": SpecialistDefinition(
        id="scheduling",
        name="Scheduling Agent",
        description="Manages scheduled tasks, cron jobs, and recurring operations.",
        category=SpecialistCategory.AUTOMATION,
        port=8085,
        env_url_key="SCHEDULING_AGENT_URL",
        is_critical=False,
        tools=[
            SpecialistTool(
                name="schedule_task",
                description="Schedule a recurring or one-time task.",
                endpoint="/schedule",
                method="POST",
                parameters=[
                    ToolParameter(name="task_type", description="Type of task to schedule", required=True),
                    ToolParameter(name="cron", description="Cron expression for recurring tasks"),
                    ToolParameter(name="run_at", description="ISO datetime for one-time tasks"),
                    ToolParameter(name="payload", description="Task payload")
                ]
            ),
            SpecialistTool(
                name="list_scheduled_tasks",
                description="List all scheduled tasks.",
                endpoint="/tasks",
                method="GET",
                parameters=[]
            ),
        ]
    ),
}


# =============================================================================
# SPECIALIST REGISTRY
# =============================================================================

class SpecialistRegistry:
    """
    Production-ready registry for managing specialist agents.
    
    Features:
    - Dynamic agent registration and discovery
    - Health monitoring with circuit breaker pattern
    - Tool capability mapping
    - Dependency tracking
    """
    
    def __init__(self, health_check_interval: int = 30):
        self._definitions = SPECIALIST_DEFINITIONS.copy()
        self._health: Dict[str, SpecialistHealth] = {}
        self._urls: Dict[str, str] = {}
        self._health_check_interval = health_check_interval
        self._health_check_task: Optional[asyncio.Task] = None
        self._initialized = False
        
        # Load URLs from environment
        self._load_urls_from_env()
        
        logger.info(f"SpecialistRegistry initialized with {len(self._definitions)} specialists")
    
    def _load_urls_from_env(self):
        """Load specialist URLs from environment variables"""
        for spec_id, definition in self._definitions.items():
            url = os.environ.get(definition.env_url_key)
            if url:
                self._urls[spec_id] = url
            else:
                # Default to localhost with defined port for development
                self._urls[spec_id] = f"http://localhost:{definition.port}"
            
            # Initialize health status
            self._health[spec_id] = SpecialistHealth()
    
    @property
    def all_specialists(self) -> Dict[str, SpecialistDefinition]:
        """Get all registered specialist definitions"""
        return self._definitions.copy()
    
    @property
    def critical_specialists(self) -> List[str]:
        """Get list of critical specialist IDs"""
        return [s.id for s in self._definitions.values() if s.is_critical]
    
    def get_definition(self, specialist_id: str) -> Optional[SpecialistDefinition]:
        """Get definition for a specialist"""
        return self._definitions.get(specialist_id)
    
    def get_url(self, specialist_id: str) -> Optional[str]:
        """Get URL for a specialist"""
        return self._urls.get(specialist_id)
    
    def get_health(self, specialist_id: str) -> Optional[SpecialistHealth]:
        """Get health status for a specialist"""
        return self._health.get(specialist_id)
    
    def get_tool(self, tool_name: str) -> Optional[tuple]:
        """
        Find a tool by name across all specialists.
        
        Returns:
            Tuple of (specialist_id, SpecialistTool) or None
        """
        for spec_id, definition in self._definitions.items():
            for tool in definition.tools:
                if tool.name == tool_name:
                    return (spec_id, tool)
        return None
    
    def get_all_tools(self) -> Dict[str, tuple]:
        """
        Get all available tools across all specialists.
        
        Returns:
            Dict mapping tool_name -> (specialist_id, SpecialistTool)
        """
        tools = {}
        for spec_id, definition in self._definitions.items():
            for tool in definition.tools:
                tools[tool.name] = (spec_id, tool)
        return tools
    
    def get_tools_description(self) -> str:
        """Generate tools description for LLM prompt"""
        lines = ["Available tools:"]
        for spec_id, definition in self._definitions.items():
            lines.append(f"\n## {definition.name}")
            for tool in definition.tools:
                params = ", ".join(tool.required_params) if tool.required_params else "none"
                lines.append(f"- {tool.name}: {tool.description}")
                lines.append(f"  Required params: {params}")
        return "\n".join(lines)
    
    async def check_health(self, specialist_id: str) -> SpecialistHealth:
        """Check health of a single specialist"""
        if specialist_id not in self._definitions:
            return SpecialistHealth(
                status=SpecialistStatus.UNKNOWN,
                error_message=f"Unknown specialist: {specialist_id}"
            )
        
        definition = self._definitions[specialist_id]
        url = self._urls.get(specialist_id)
        health = self._health.get(specialist_id, SpecialistHealth())
        
        try:
            start_time = datetime.now(timezone.utc)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{url}{definition.health_path}")
                
            end_time = datetime.now(timezone.utc)
            response_time = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                health.status = SpecialistStatus.HEALTHY
                health.consecutive_failures = 0
                health.error_message = None
                try:
                    health.metadata = response.json()
                except:
                    health.metadata = {}
            else:
                health.status = SpecialistStatus.DEGRADED
                health.consecutive_failures += 1
                health.error_message = f"HTTP {response.status_code}"
            
            health.response_time_ms = response_time
            health.last_check = end_time
            
        except httpx.ConnectError:
            health.status = SpecialistStatus.UNHEALTHY
            health.consecutive_failures += 1
            health.error_message = "Connection refused"
            health.last_check = datetime.now(timezone.utc)
        except httpx.TimeoutException:
            health.status = SpecialistStatus.UNHEALTHY
            health.consecutive_failures += 1
            health.error_message = "Timeout"
            health.last_check = datetime.now(timezone.utc)
        except Exception as e:
            health.status = SpecialistStatus.UNHEALTHY
            health.consecutive_failures += 1
            health.error_message = str(e)
            health.last_check = datetime.now(timezone.utc)
        
        self._health[specialist_id] = health
        return health
    
    async def check_all_health(self) -> Dict[str, SpecialistHealth]:
        """Check health of all specialists"""
        tasks = [self.check_health(spec_id) for spec_id in self._definitions.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for spec_id, result in zip(self._definitions.keys(), results):
            if isinstance(result, Exception):
                self._health[spec_id] = SpecialistHealth(
                    status=SpecialistStatus.UNHEALTHY,
                    error_message=str(result),
                    last_check=datetime.now(timezone.utc)
                )
        
        return self._health.copy()
    
    async def verify_critical_specialists(self) -> tuple:
        """
        Verify that all critical specialists are healthy.
        
        Returns:
            Tuple of (all_healthy: bool, unhealthy_list: List[str])
        """
        await self.check_all_health()
        
        unhealthy = []
        for spec_id in self.critical_specialists:
            health = self._health.get(spec_id)
            if not health or health.status != SpecialistStatus.HEALTHY:
                unhealthy.append(spec_id)
        
        return (len(unhealthy) == 0, unhealthy)
    
    async def start_health_monitoring(self):
        """Start background health monitoring"""
        if self._health_check_task is not None:
            return
        
        async def monitor():
            while True:
                try:
                    await self.check_all_health()
                    logger.debug("Health check completed for all specialists")
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self._health_check_interval)
        
        self._health_check_task = asyncio.create_task(monitor())
        logger.info(f"Started health monitoring (interval: {self._health_check_interval}s)")
    
    async def stop_health_monitoring(self):
        """Stop background health monitoring"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Stopped health monitoring")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of all specialist statuses"""
        summary = {
            "total": len(self._definitions),
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "unknown": 0,
            "specialists": {}
        }
        
        for spec_id, health in self._health.items():
            summary[health.status.value] += 1
            definition = self._definitions.get(spec_id)
            summary["specialists"][spec_id] = {
                "name": definition.name if definition else spec_id,
                "status": health.status.value,
                "category": definition.category.value if definition else "unknown",
                "is_critical": definition.is_critical if definition else False,
                "response_time_ms": health.response_time_ms,
                "last_check": health.last_check.isoformat() if health.last_check else None,
                "error": health.error_message,
                "tool_count": len(definition.tools) if definition else 0
            }
        
        return summary
    
    def register_specialist(
        self,
        specialist_id: str,
        url: str,
        definition: Optional[SpecialistDefinition] = None
    ):
        """
        Register a new specialist or update existing URL.
        
        Args:
            specialist_id: Unique identifier for the specialist
            url: Base URL for the specialist
            definition: Optional full definition (if adding a new specialist)
        """
        self._urls[specialist_id] = url
        
        if definition:
            self._definitions[specialist_id] = definition
        
        if specialist_id not in self._health:
            self._health[specialist_id] = SpecialistHealth()
        
        logger.info(f"Registered specialist: {specialist_id} at {url}")
    
    def unregister_specialist(self, specialist_id: str):
        """Remove a specialist from the registry"""
        self._urls.pop(specialist_id, None)
        self._definitions.pop(specialist_id, None)
        self._health.pop(specialist_id, None)
        logger.info(f"Unregistered specialist: {specialist_id}")


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# Global registry instance
specialist_registry = SpecialistRegistry()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def get_healthy_specialists() -> List[str]:
    """Get list of currently healthy specialist IDs"""
    return [
        spec_id 
        for spec_id, health in specialist_registry._health.items()
        if health.status == SpecialistStatus.HEALTHY
    ]


async def is_specialist_available(specialist_id: str) -> bool:
    """Check if a specialist is currently available"""
    health = await specialist_registry.check_health(specialist_id)
    return health.status == SpecialistStatus.HEALTHY


def get_specialist_for_tool(tool_name: str) -> Optional[str]:
    """Get the specialist ID that provides a given tool"""
    result = specialist_registry.get_tool(tool_name)
    return result[0] if result else None

