"""
Nexus Jira Hygiene Agent - MCP Server Implementation
=====================================================

Proactive Jira data quality agent exposed via MCP over SSE.
Monitors ticket hygiene, sends notifications, and provides fix recommendations.

Architecture: MCP Server with SSE Transport
Port: 8085
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json
import random

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import uvicorn
import httpx

# Add shared lib path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'shared'))

try:
    from nexus_lib.config import ConfigManager, ConfigKeys
except ImportError:
    ConfigManager = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nexus.jira-hygiene-agent")

# =============================================================================
# Configuration
# =============================================================================

JIRA_URL = os.getenv("JIRA_URL", "https://your-org.atlassian.net")
JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_MOCK_MODE = os.getenv("JIRA_MOCK_MODE", "true").lower() == "true"
SLACK_AGENT_URL = os.getenv("SLACK_AGENT_URL", "http://slack-agent:8084")
HYGIENE_CHECK_SCHEDULE = os.getenv("HYGIENE_CHECK_SCHEDULE", "0 9 * * 1-5")  # 9am weekdays
PORT = int(os.getenv("JIRA_HYGIENE_AGENT_PORT", "8085"))

# Hygiene validation rules
REQUIRED_FIELDS = {
    "labels": "labels",
    "fix_version": "fixVersions",
    "story_points": "customfield_10016",
    "team": "customfield_10001",
}

# =============================================================================
# Mock Data Generator
# =============================================================================

class MockHygieneData:
    """Generates realistic mock hygiene data."""
    
    VIOLATIONS = [
        "Missing labels",
        "Missing fix version",
        "Missing story points",
        "Missing team assignment",
        "Stale ticket (no update in 14+ days)",
        "Missing acceptance criteria"
    ]
    
    ASSIGNEES = [
        {"email": "alice@example.com", "display_name": "Alice Smith", "account_id": "user-001"},
        {"email": "bob@example.com", "display_name": "Bob Jones", "account_id": "user-002"},
        {"email": "carol@example.com", "display_name": "Carol White", "account_id": "user-003"},
        {"email": "david@example.com", "display_name": "David Brown", "account_id": "user-004"},
    ]
    
    @classmethod
    def generate_violation(cls, ticket_key: str) -> Dict[str, Any]:
        """Generate a mock hygiene violation."""
        violation_type = random.choice(cls.VIOLATIONS)
        assignee = random.choice(cls.ASSIGNEES)
        
        return {
            "ticket_key": ticket_key,
            "summary": f"Sample ticket {ticket_key}",
            "violation_type": violation_type,
            "severity": random.choice(["high", "medium", "low"]),
            "assignee": assignee,
            "assignee_email": assignee["email"],
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
            "last_updated": (datetime.utcnow() - timedelta(days=random.randint(0, 14))).isoformat(),
            "recommendation": f"Please update the ticket to include {violation_type.lower().replace('missing ', '')}"
        }
    
    @classmethod
    def generate_project_hygiene(cls, project_key: str) -> Dict[str, Any]:
        """Generate mock project hygiene report."""
        total_tickets = random.randint(30, 80)
        violations_count = random.randint(5, 20)
        compliant = total_tickets - violations_count
        
        violations = [
            cls.generate_violation(f"{project_key}-{random.randint(100, 999)}")
            for _ in range(violations_count)
        ]
        
        # Group by assignee
        by_assignee = {}
        for v in violations:
            email = v["assignee_email"]
            if email not in by_assignee:
                by_assignee[email] = {
                    "assignee": v["assignee"],
                    "violations": []
                }
            by_assignee[email]["violations"].append(v)
        
        # Calculate score
        hygiene_score = round((compliant / total_tickets) * 100, 1)
        
        return {
            "project_key": project_key,
            "hygiene_score": hygiene_score,
            "total_tickets": total_tickets,
            "compliant_tickets": compliant,
            "violations_count": violations_count,
            "violations": violations,
            "by_assignee": list(by_assignee.values()),
            "violation_breakdown": {
                "missing_labels": sum(1 for v in violations if "labels" in v["violation_type"].lower()),
                "missing_fix_version": sum(1 for v in violations if "fix version" in v["violation_type"].lower()),
                "missing_story_points": sum(1 for v in violations if "story points" in v["violation_type"].lower()),
                "missing_team": sum(1 for v in violations if "team" in v["violation_type"].lower()),
                "stale_tickets": sum(1 for v in violations if "stale" in v["violation_type"].lower()),
            },
            "checked_at": datetime.utcnow().isoformat(),
            "trend": random.choice(["improving", "stable", "declining"])
        }

# =============================================================================
# Hygiene Checker
# =============================================================================

class HygieneChecker:
    """Validates Jira ticket hygiene."""
    
    def __init__(self, jira_url: str, username: str, api_token: str, mock_mode: bool = False):
        self.jira_url = jira_url.rstrip("/")
        self.username = username
        self.api_token = api_token
        self.mock_mode = mock_mode
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            auth = (self.username, self.api_token) if self.username and self.api_token else None
            self._client = httpx.AsyncClient(
                base_url=f"{self.jira_url}/rest/api/3",
                auth=auth,
                timeout=30.0,
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def check_project_hygiene(self, project_key: str) -> Dict[str, Any]:
        """Check hygiene for all active tickets in a project."""
        if self.mock_mode:
            return MockHygieneData.generate_project_hygiene(project_key)
        
        client = await self._get_client()
        
        # Fetch active tickets
        jql = f'project = "{project_key}" AND status NOT IN (Done, Closed, Resolved) ORDER BY updated DESC'
        response = await client.post("/search", json={
            "jql": jql,
            "maxResults": 200,
            "fields": ["summary", "assignee", "labels", "fixVersions", "customfield_10016", "customfield_10001", "updated"]
        })
        response.raise_for_status()
        data = response.json()
        
        issues = data.get("issues", [])
        violations = []
        
        for issue in issues:
            fields = issue.get("fields", {})
            issue_violations = []
            
            # Check required fields
            if not fields.get("labels"):
                issue_violations.append("Missing labels")
            
            if not fields.get("fixVersions"):
                issue_violations.append("Missing fix version")
            
            if fields.get("customfield_10016") is None:
                issue_violations.append("Missing story points")
            
            if not fields.get("customfield_10001"):
                issue_violations.append("Missing team assignment")
            
            # Check for staleness
            updated = fields.get("updated")
            if updated:
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if (datetime.now(updated_dt.tzinfo) - updated_dt).days > 14:
                    issue_violations.append("Stale ticket (no update in 14+ days)")
            
            if issue_violations:
                assignee = fields.get("assignee") or {}
                for violation_type in issue_violations:
                    violations.append({
                        "ticket_key": issue["key"],
                        "summary": fields.get("summary", ""),
                        "violation_type": violation_type,
                        "severity": "high" if "stale" in violation_type.lower() or "labels" in violation_type.lower() else "medium",
                        "assignee": {
                            "account_id": assignee.get("accountId", ""),
                            "display_name": assignee.get("displayName", "Unassigned"),
                            "email": assignee.get("emailAddress", "")
                        },
                        "assignee_email": assignee.get("emailAddress", ""),
                        "last_updated": fields.get("updated")
                    })
        
        # Group by assignee
        by_assignee = {}
        for v in violations:
            email = v["assignee_email"]
            if email not in by_assignee:
                by_assignee[email] = {
                    "assignee": v["assignee"],
                    "violations": []
                }
            by_assignee[email]["violations"].append(v)
        
        compliant = len(issues) - len(set(v["ticket_key"] for v in violations))
        hygiene_score = round((compliant / len(issues)) * 100, 1) if issues else 100
        
        return {
            "project_key": project_key,
            "hygiene_score": hygiene_score,
            "total_tickets": len(issues),
            "compliant_tickets": compliant,
            "violations_count": len(violations),
            "violations": violations,
            "by_assignee": list(by_assignee.values()),
            "checked_at": datetime.utcnow().isoformat()
        }
    
    async def get_user_violations(self, project_key: str, user_email: str) -> Dict[str, Any]:
        """Get violations for a specific user."""
        hygiene = await self.check_project_hygiene(project_key)
        
        user_violations = [
            v for v in hygiene["violations"]
            if v["assignee_email"] == user_email
        ]
        
        return {
            "user_email": user_email,
            "project_key": project_key,
            "violations": user_violations,
            "violations_count": len(user_violations),
            "checked_at": datetime.utcnow().isoformat()
        }
    
    async def get_fix_recommendations(self, ticket_key: str) -> Dict[str, Any]:
        """Get fix recommendations for a ticket."""
        if self.mock_mode:
            violation = MockHygieneData.generate_violation(ticket_key)
            return {
                "ticket_key": ticket_key,
                "violations": [violation["violation_type"]],
                "recommendations": [
                    {"field": "labels", "suggestion": "Add appropriate labels (e.g., backend, frontend, api)"},
                    {"field": "fixVersions", "suggestion": "Set the target release version"},
                    {"field": "story_points", "suggestion": "Estimate story points using Fibonacci scale"},
                ],
                "quick_fixes": {
                    "suggested_labels": ["backend", "feature"],
                    "suggested_fix_version": "v2.0.0",
                    "suggested_story_points": 5
                }
            }
        
        # In real mode, fetch ticket and analyze
        client = await self._get_client()
        response = await client.get(f"/issue/{ticket_key}")
        response.raise_for_status()
        issue = response.json()
        
        fields = issue.get("fields", {})
        recommendations = []
        
        if not fields.get("labels"):
            recommendations.append({
                "field": "labels",
                "suggestion": "Add labels for categorization (e.g., backend, frontend, api, security)"
            })
        
        if not fields.get("fixVersions"):
            recommendations.append({
                "field": "fixVersions",
                "suggestion": "Set the target release version for this ticket"
            })
        
        if fields.get("customfield_10016") is None:
            recommendations.append({
                "field": "story_points",
                "suggestion": "Estimate story points (1, 2, 3, 5, 8, 13, 21)"
            })
        
        return {
            "ticket_key": ticket_key,
            "summary": fields.get("summary", ""),
            "recommendations": recommendations,
            "current_values": {
                "labels": fields.get("labels", []),
                "fix_versions": [v.get("name") for v in fields.get("fixVersions", [])],
                "story_points": fields.get("customfield_10016")
            }
        }

# =============================================================================
# Notification Service
# =============================================================================

class NotificationService:
    """Sends hygiene notifications via Slack agent."""
    
    def __init__(self, slack_agent_url: str):
        self.slack_agent_url = slack_agent_url.rstrip("/")
    
    async def notify_user(self, user_email: str, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send hygiene notification to a user via Slack DM."""
        if not violations:
            return {"sent": False, "reason": "No violations to notify"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Format message
                tickets = list(set(v["ticket_key"] for v in violations))
                message = f"🔔 *Jira Hygiene Alert*\n\nYou have {len(violations)} hygiene issue(s) in {len(tickets)} ticket(s):\n\n"
                
                for ticket_key in tickets[:5]:  # Limit to 5 tickets
                    ticket_violations = [v for v in violations if v["ticket_key"] == ticket_key]
                    message += f"• *{ticket_key}*: {', '.join(v['violation_type'] for v in ticket_violations)}\n"
                
                if len(tickets) > 5:
                    message += f"\n...and {len(tickets) - 5} more tickets."
                
                message += "\n\nPlease update your tickets to maintain project hygiene! 🧹"
                
                response = await client.post(
                    f"{self.slack_agent_url}/execute",
                    json={
                        "action": "send_dm",
                        "payload": {
                            "email": user_email,
                            "message": message,
                            "blocks": [
                                {
                                    "type": "section",
                                    "text": {"type": "mrkdwn", "text": message}
                                },
                                {
                                    "type": "actions",
                                    "elements": [
                                        {
                                            "type": "button",
                                            "text": {"type": "plain_text", "text": "Fix Tickets Now"},
                                            "action_id": "hygiene_fix_modal",
                                            "style": "primary"
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                )
                
                if response.status_code == 200:
                    return {"sent": True, "user_email": user_email, "violations_count": len(violations)}
                else:
                    return {"sent": False, "error": f"Slack agent returned {response.status_code}"}
        
        except Exception as e:
            logger.error(f"Failed to send notification to {user_email}: {e}")
            return {"sent": False, "error": str(e)}
    
    async def notify_channel(self, channel: str, hygiene_report: Dict[str, Any]) -> Dict[str, Any]:
        """Send hygiene summary to a Slack channel."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                score = hygiene_report.get("hygiene_score", 0)
                emoji = "🟢" if score >= 90 else "🟡" if score >= 70 else "🔴"
                
                message = f"{emoji} *Project Hygiene Report: {hygiene_report['project_key']}*\n\n"
                message += f"• Score: *{score}%*\n"
                message += f"• Compliant Tickets: {hygiene_report['compliant_tickets']}/{hygiene_report['total_tickets']}\n"
                message += f"• Issues Found: {hygiene_report['violations_count']}\n"
                
                response = await client.post(
                    f"{self.slack_agent_url}/execute",
                    json={
                        "action": "notify",
                        "payload": {
                            "channel": channel,
                            "message": message
                        }
                    }
                )
                
                return {"sent": response.status_code == 200, "channel": channel}
        
        except Exception as e:
            logger.error(f"Failed to send channel notification: {e}")
            return {"sent": False, "error": str(e)}

# =============================================================================
# Initialize Services
# =============================================================================

hygiene_checker = HygieneChecker(
    jira_url=JIRA_URL,
    username=JIRA_USERNAME,
    api_token=JIRA_API_TOKEN,
    mock_mode=JIRA_MOCK_MODE
)

notification_service = NotificationService(slack_agent_url=SLACK_AGENT_URL)

# Scheduler for automated checks
scheduler = AsyncIOScheduler()

# Create MCP server
mcp_server = Server("nexus-jira-hygiene-agent")

# =============================================================================
# Scheduled Jobs
# =============================================================================

async def scheduled_hygiene_check():
    """Run scheduled hygiene check for all configured projects."""
    logger.info("Running scheduled hygiene check...")
    
    # In production, this would fetch project keys from config
    project_keys = os.getenv("HYGIENE_PROJECT_KEYS", "PROJ,NEXUS").split(",")
    
    for project_key in project_keys:
        try:
            hygiene = await hygiene_checker.check_project_hygiene(project_key.strip())
            logger.info(f"Project {project_key}: Score={hygiene['hygiene_score']}%, Violations={hygiene['violations_count']}")
            
            # Notify each assignee with violations
            for assignee_data in hygiene.get("by_assignee", []):
                email = assignee_data["assignee"].get("email")
                if email:
                    await notification_service.notify_user(email, assignee_data["violations"])
        
        except Exception as e:
            logger.error(f"Failed hygiene check for {project_key}: {e}")

# =============================================================================
# MCP Tool Definitions
# =============================================================================

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available hygiene tools."""
    return [
        Tool(
            name="check_project_hygiene",
            description="Run a comprehensive hygiene check on a Jira project. Returns hygiene score, violations by category, and per-assignee breakdown.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "Jira project key (e.g., PROJ, NEXUS)"
                    }
                },
                "required": ["project_key"]
            }
        ),
        Tool(
            name="get_user_violations",
            description="Get hygiene violations for a specific user in a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "Jira project key"
                    },
                    "user_email": {
                        "type": "string",
                        "description": "User's email address"
                    }
                },
                "required": ["project_key", "user_email"]
            }
        ),
        Tool(
            name="get_fix_recommendations",
            description="Get specific recommendations for fixing hygiene issues on a ticket.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_key": {
                        "type": "string",
                        "description": "Jira ticket key"
                    }
                },
                "required": ["ticket_key"]
            }
        ),
        Tool(
            name="notify_hygiene_issues",
            description="Send hygiene notifications to users or channels via Slack.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "Jira project key"
                    },
                    "notify_users": {
                        "type": "boolean",
                        "description": "Send DMs to users with violations",
                        "default": True
                    },
                    "notify_channel": {
                        "type": "string",
                        "description": "Optional Slack channel for summary"
                    }
                },
                "required": ["project_key"]
            }
        ),
        Tool(
            name="run_hygiene_check",
            description="Manually trigger a hygiene check (same as scheduled check).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of project keys to check"
                    }
                },
                "required": []
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a hygiene tool."""
    logger.info(f"Tool call: {name} with args: {arguments}")
    
    try:
        if name == "check_project_hygiene":
            result = await hygiene_checker.check_project_hygiene(arguments["project_key"])
        
        elif name == "get_user_violations":
            result = await hygiene_checker.get_user_violations(
                project_key=arguments["project_key"],
                user_email=arguments["user_email"]
            )
        
        elif name == "get_fix_recommendations":
            result = await hygiene_checker.get_fix_recommendations(arguments["ticket_key"])
        
        elif name == "notify_hygiene_issues":
            project_key = arguments["project_key"]
            hygiene = await hygiene_checker.check_project_hygiene(project_key)
            
            notifications_sent = []
            
            if arguments.get("notify_users", True):
                for assignee_data in hygiene.get("by_assignee", []):
                    email = assignee_data["assignee"].get("email")
                    if email:
                        notif_result = await notification_service.notify_user(email, assignee_data["violations"])
                        notifications_sent.append(notif_result)
            
            if arguments.get("notify_channel"):
                channel_result = await notification_service.notify_channel(
                    arguments["notify_channel"],
                    hygiene
                )
                notifications_sent.append(channel_result)
            
            result = {
                "project_key": project_key,
                "hygiene_score": hygiene["hygiene_score"],
                "notifications_sent": len([n for n in notifications_sent if n.get("sent")]),
                "notifications": notifications_sent
            }
        
        elif name == "run_hygiene_check":
            project_keys = arguments.get("project_keys") or os.getenv("HYGIENE_PROJECT_KEYS", "PROJ").split(",")
            results = []
            
            for pk in project_keys:
                hygiene = await hygiene_checker.check_project_hygiene(pk.strip())
                results.append({
                    "project_key": pk.strip(),
                    "hygiene_score": hygiene["hygiene_score"],
                    "violations_count": hygiene["violations_count"]
                })
            
            result = {"checked_projects": results, "checked_at": datetime.utcnow().isoformat()}
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

# =============================================================================
# Starlette App
# =============================================================================

async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "nexus-jira-hygiene-agent",
        "version": "2.0.0",
        "transport": "mcp-sse",
        "mock_mode": JIRA_MOCK_MODE,
        "scheduler_running": scheduler.running,
        "next_run": str(scheduler.get_jobs()[0].next_run_time) if scheduler.get_jobs() else None,
        "timestamp": datetime.utcnow().isoformat()
    })

async def sse_endpoint(request: Request):
    """SSE endpoint for MCP communication."""
    transport = SseServerTransport("/messages")
    async with transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp_server.run(
            streams[0],
            streams[1],
            mcp_server.create_initialization_options()
        )

async def legacy_execute(request: Request) -> JSONResponse:
    """Legacy REST endpoint for backward compatibility."""
    try:
        body = await request.json()
        action = body.get("action", "")
        payload = body.get("payload", {})
        
        action_map = {
            "check_hygiene": ("check_project_hygiene", {"project_key": payload.get("project_key")}),
            "get_violations": ("get_user_violations", {"project_key": payload.get("project_key"), "user_email": payload.get("user_email")}),
            "get_recommendations": ("get_fix_recommendations", {"ticket_key": payload.get("ticket_key")}),
            "run_check": ("run_hygiene_check", {"project_keys": payload.get("project_keys")}),
        }
        
        if action not in action_map:
            return JSONResponse({"error": f"Unknown action: {action}"}, status_code=400)
        
        tool_name, tool_args = action_map[action]
        result = await call_tool(tool_name, tool_args)
        
        return JSONResponse({
            "status": "success",
            "data": json.loads(result[0].text) if result else {},
            "agent_type": "jira_hygiene"
        })
    
    except Exception as e:
        logger.error(f"Execute error: {e}")
        return JSONResponse({
            "status": "failed",
            "error_message": str(e),
            "agent_type": "jira_hygiene"
        }, status_code=500)

async def manual_run(request: Request) -> JSONResponse:
    """Manually trigger hygiene check."""
    await scheduled_hygiene_check()
    return JSONResponse({"message": "Hygiene check triggered"})

async def startup():
    """Start the scheduler."""
    if HYGIENE_CHECK_SCHEDULE:
        try:
            parts = HYGIENE_CHECK_SCHEDULE.split()
            trigger = CronTrigger(
                minute=parts[0] if len(parts) > 0 else "0",
                hour=parts[1] if len(parts) > 1 else "9",
                day=parts[2] if len(parts) > 2 else "*",
                month=parts[3] if len(parts) > 3 else "*",
                day_of_week=parts[4] if len(parts) > 4 else "1-5"
            )
            scheduler.add_job(scheduled_hygiene_check, trigger, id="hygiene_check")
            scheduler.start()
            logger.info(f"Scheduler started with schedule: {HYGIENE_CHECK_SCHEDULE}")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")

async def shutdown():
    """Stop the scheduler and cleanup."""
    scheduler.shutdown(wait=False)
    await hygiene_checker.close()

app = Starlette(
    debug=os.getenv("NEXUS_ENV", "development") == "development",
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/sse", sse_endpoint, methods=["GET"]),
        Route("/execute", legacy_execute, methods=["POST"]),
        Route("/run-check", manual_run, methods=["POST"]),
        Route("/", health_check, methods=["GET"]),
    ],
    on_startup=[startup],
    on_shutdown=[shutdown]
)

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info(f"🚀 Starting Nexus Jira Hygiene Agent (MCP over SSE) on port {PORT}")
    logger.info(f"📡 Mock mode: {JIRA_MOCK_MODE}")
    logger.info(f"📅 Schedule: {HYGIENE_CHECK_SCHEDULE}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
