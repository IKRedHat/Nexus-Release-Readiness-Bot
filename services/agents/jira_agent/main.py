"""
Nexus Jira Agent - MCP Server Implementation
=============================================

Jira integration agent exposed via Model Context Protocol (MCP) over SSE.
Provides tools for ticket management, sprint stats, and JQL search.

Architecture: MCP Server with SSE Transport
Port: 8081
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
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.requests import Request
from pydantic import BaseModel, Field
import uvicorn
import httpx

# Add shared lib path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'shared'))

try:
    from nexus_lib.config import ConfigManager, ConfigKeys
    from nexus_lib.schemas.agent_contract import (
        JiraTicket, JiraSprintStats, JiraSearchResult, JiraUser,
        JiraIssueType, AgentTaskRequest, AgentTaskResponse, TaskStatus, AgentType
    )
except ImportError:
    ConfigManager = None
    # Define minimal fallback models
    class JiraTicket(BaseModel):
        key: str
        summary: str
        status: str
        issue_type: str = "Task"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nexus.jira-agent")

# =============================================================================
# Configuration
# =============================================================================

JIRA_URL = os.getenv("JIRA_URL", "https://your-org.atlassian.net")
JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_MOCK_MODE = os.getenv("JIRA_MOCK_MODE", "true").lower() == "true"
PORT = int(os.getenv("JIRA_AGENT_PORT", "8081"))

# =============================================================================
# Mock Data Generator
# =============================================================================

class MockJiraData:
    """Generates realistic mock Jira data for development."""
    
    STATUSES = ["To Do", "In Progress", "In Review", "Done", "Blocked"]
    ISSUE_TYPES = ["Epic", "Story", "Task", "Bug", "Sub-task"]
    PRIORITIES = ["Critical", "High", "Medium", "Low"]
    LABELS = ["backend", "frontend", "api", "security", "performance", "tech-debt"]
    TEAMS = ["Platform", "Mobile", "Infrastructure", "Data", "DevOps"]
    
    @classmethod
    def generate_ticket(cls, key: str, **overrides) -> Dict[str, Any]:
        """Generate a mock Jira ticket."""
        project_key = key.split("-")[0] if "-" in key else "PROJ"
        issue_number = key.split("-")[1] if "-" in key else str(random.randint(100, 999))
        
        ticket = {
            "key": key,
            "id": str(random.randint(10000, 99999)),
            "summary": f"[{project_key}] Sample issue #{issue_number}",
            "description": f"Description for issue {key}. This is a mock ticket for development.",
            "issue_type": random.choice(cls.ISSUE_TYPES),
            "status": random.choice(cls.STATUSES),
            "priority": random.choice(cls.PRIORITIES),
            "project_key": project_key,
            "labels": random.sample(cls.LABELS, k=random.randint(0, 3)),
            "story_points": random.choice([1, 2, 3, 5, 8, 13, None]),
            "fix_versions": [f"v{random.randint(1, 3)}.{random.randint(0, 9)}.0"],
            "assignee": {
                "account_id": f"user-{random.randint(1000, 9999)}",
                "display_name": random.choice(["Alice Smith", "Bob Jones", "Carol White", "David Brown"]),
                "email": f"dev{random.randint(1, 10)}@example.com",
                "active": True
            },
            "reporter": {
                "account_id": f"user-{random.randint(1000, 9999)}",
                "display_name": "John Doe",
                "email": "john.doe@example.com",
                "active": True
            },
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "components": random.sample(cls.TEAMS, k=random.randint(0, 2)),
            "custom_fields": {
                "team": random.choice(cls.TEAMS)
            }
        }
        ticket.update(overrides)
        return ticket
    
    @classmethod
    def generate_sprint_stats(cls, project_key: str, sprint_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate mock sprint statistics."""
        total = random.randint(20, 50)
        completed = random.randint(int(total * 0.6), total)
        in_progress = random.randint(0, total - completed)
        blocked = total - completed - in_progress
        
        total_points = random.uniform(30, 80)
        completed_points = total_points * (completed / total) * random.uniform(0.9, 1.1)
        
        return {
            "sprint_id": sprint_id or random.randint(100, 999),
            "sprint_name": f"Sprint {random.randint(1, 52)} - {project_key}",
            "total_issues": total,
            "completed_issues": completed,
            "in_progress_issues": in_progress,
            "blocked_issues": blocked,
            "total_story_points": round(total_points, 1),
            "completed_story_points": round(completed_points, 1),
            "completion_percentage": round((completed / total) * 100, 1),
            "blockers": [f"{project_key}-{random.randint(100, 999)}" for _ in range(blocked)]
        }
    
    @classmethod
    def generate_hierarchy(cls, epic_key: str) -> Dict[str, Any]:
        """Generate mock epic hierarchy."""
        project_key = epic_key.split("-")[0]
        num_stories = random.randint(3, 8)
        
        stories = []
        for i in range(num_stories):
            story_key = f"{project_key}-{random.randint(100, 999)}"
            num_subtasks = random.randint(0, 4)
            subtasks = [
                cls.generate_ticket(f"{project_key}-{random.randint(100, 999)}", 
                                   issue_type="Sub-task", parent_key=story_key)
                for _ in range(num_subtasks)
            ]
            story = cls.generate_ticket(story_key, issue_type="Story", epic_key=epic_key)
            story["subtasks"] = subtasks
            stories.append(story)
        
        epic = cls.generate_ticket(epic_key, issue_type="Epic")
        epic["children"] = stories
        
        return epic

# =============================================================================
# Jira API Client
# =============================================================================

class JiraClient:
    """Jira REST API client with mock fallback."""
    
    def __init__(self, base_url: str, username: str, api_token: str, mock_mode: bool = False):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.api_token = api_token
        self.mock_mode = mock_mode
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            auth = (self.username, self.api_token) if self.username and self.api_token else None
            self._client = httpx.AsyncClient(
                base_url=f"{self.base_url}/rest/api/3",
                auth=auth,
                timeout=30.0,
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get_issue(self, key: str) -> Dict[str, Any]:
        """Fetch a single Jira issue."""
        if self.mock_mode:
            return MockJiraData.generate_ticket(key)
        
        client = await self._get_client()
        response = await client.get(f"/issue/{key}")
        response.raise_for_status()
        return self._parse_issue(response.json())
    
    async def search_issues(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        """Search issues using JQL."""
        if self.mock_mode:
            # Parse project key from JQL if present
            project_key = "PROJ"
            if "project" in jql.lower():
                parts = jql.split("=")
                if len(parts) > 1:
                    project_key = parts[1].strip().strip('"').strip("'").split()[0]
            
            issues = [MockJiraData.generate_ticket(f"{project_key}-{i}") for i in range(random.randint(5, max_results))]
            return {
                "total": len(issues),
                "start_at": 0,
                "max_results": max_results,
                "issues": issues
            }
        
        client = await self._get_client()
        response = await client.post("/search", json={
            "jql": jql,
            "maxResults": max_results,
            "fields": ["*all"]
        })
        response.raise_for_status()
        data = response.json()
        return {
            "total": data.get("total", 0),
            "start_at": data.get("startAt", 0),
            "max_results": data.get("maxResults", max_results),
            "issues": [self._parse_issue(issue) for issue in data.get("issues", [])]
        }
    
    async def get_sprint_stats(self, project_key: str, sprint_id: Optional[int] = None) -> Dict[str, Any]:
        """Get sprint statistics for a project."""
        if self.mock_mode:
            return MockJiraData.generate_sprint_stats(project_key, sprint_id)
        
        # Real implementation would query Jira Agile API
        jql = f'project = "{project_key}" AND sprint in openSprints()'
        result = await self.search_issues(jql, max_results=200)
        
        issues = result.get("issues", [])
        completed = sum(1 for i in issues if i.get("status", "").lower() in ["done", "closed"])
        in_progress = sum(1 for i in issues if i.get("status", "").lower() in ["in progress", "in review"])
        blocked = sum(1 for i in issues if i.get("status", "").lower() == "blocked")
        
        total_points = sum(i.get("story_points") or 0 for i in issues)
        completed_points = sum(i.get("story_points") or 0 for i in issues if i.get("status", "").lower() in ["done", "closed"])
        
        return {
            "sprint_id": sprint_id or 0,
            "sprint_name": f"Current Sprint - {project_key}",
            "total_issues": len(issues),
            "completed_issues": completed,
            "in_progress_issues": in_progress,
            "blocked_issues": blocked,
            "total_story_points": total_points,
            "completed_story_points": completed_points,
            "completion_percentage": round((completed / len(issues) * 100) if issues else 0, 1),
            "blockers": [i["key"] for i in issues if i.get("status", "").lower() == "blocked"]
        }
    
    async def get_hierarchy(self, epic_key: str) -> Dict[str, Any]:
        """Get epic with all children."""
        if self.mock_mode:
            return MockJiraData.generate_hierarchy(epic_key)
        
        # Fetch epic
        epic = await self.get_issue(epic_key)
        
        # Search for stories in epic
        jql = f'"Epic Link" = {epic_key}'
        result = await self.search_issues(jql, max_results=100)
        
        stories = []
        for story in result.get("issues", []):
            # Get subtasks for each story
            subtask_jql = f'parent = {story["key"]}'
            subtask_result = await self.search_issues(subtask_jql, max_results=50)
            story["subtasks"] = subtask_result.get("issues", [])
            stories.append(story)
        
        epic["children"] = stories
        return epic
    
    async def update_issue(self, key: str, fields: Dict[str, Any], comment: Optional[str] = None) -> Dict[str, Any]:
        """Update a Jira issue."""
        if self.mock_mode:
            ticket = MockJiraData.generate_ticket(key)
            ticket.update(fields)
            return {"success": True, "key": key, "updated": ticket}
        
        client = await self._get_client()
        
        # Update fields
        if fields:
            response = await client.put(f"/issue/{key}", json={"fields": fields})
            response.raise_for_status()
        
        # Add comment
        if comment:
            await client.post(f"/issue/{key}/comment", json={
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]
                }
            })
        
        return {"success": True, "key": key}
    
    async def transition_issue(self, key: str, transition_name: str) -> Dict[str, Any]:
        """Transition a Jira issue to a new status."""
        if self.mock_mode:
            return {"success": True, "key": key, "transition": transition_name}
        
        client = await self._get_client()
        
        # Get available transitions
        response = await client.get(f"/issue/{key}/transitions")
        response.raise_for_status()
        transitions = response.json().get("transitions", [])
        
        # Find matching transition
        transition_id = None
        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                transition_id = t["id"]
                break
        
        if not transition_id:
            return {"success": False, "error": f"Transition '{transition_name}' not found"}
        
        # Perform transition
        response = await client.post(f"/issue/{key}/transitions", json={"transition": {"id": transition_id}})
        response.raise_for_status()
        
        return {"success": True, "key": key, "transition": transition_name}
    
    def _parse_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Jira API response into our schema."""
        fields = data.get("fields", {})
        return {
            "key": data.get("key"),
            "id": data.get("id"),
            "summary": fields.get("summary", ""),
            "description": self._parse_adf(fields.get("description")),
            "issue_type": fields.get("issuetype", {}).get("name", "Task"),
            "status": fields.get("status", {}).get("name", "To Do"),
            "priority": fields.get("priority", {}).get("name", "Medium"),
            "project_key": fields.get("project", {}).get("key"),
            "assignee": self._parse_user(fields.get("assignee")),
            "reporter": self._parse_user(fields.get("reporter")),
            "labels": fields.get("labels", []),
            "story_points": fields.get("customfield_10016"),  # Story points field
            "fix_versions": [v.get("name") for v in fields.get("fixVersions", [])],
            "components": [c.get("name") for c in fields.get("components", [])],
            "created_at": fields.get("created"),
            "updated_at": fields.get("updated"),
            "epic_key": fields.get("parent", {}).get("key") if fields.get("parent") else None
        }
    
    def _parse_user(self, user_data: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Parse Jira user object."""
        if not user_data:
            return None
        return {
            "account_id": user_data.get("accountId", ""),
            "display_name": user_data.get("displayName", ""),
            "email": user_data.get("emailAddress", ""),
            "active": user_data.get("active", True)
        }
    
    def _parse_adf(self, adf: Optional[Dict]) -> str:
        """Parse Atlassian Document Format to plain text."""
        if not adf:
            return ""
        if isinstance(adf, str):
            return adf
        
        # Simple ADF text extraction
        def extract_text(node: Dict) -> str:
            if not isinstance(node, dict):
                return str(node) if node else ""
            
            text = node.get("text", "")
            content = node.get("content", [])
            for child in content:
                text += extract_text(child)
            return text
        
        return extract_text(adf)

# =============================================================================
# MCP Server Setup
# =============================================================================

# Initialize Jira client
jira_client = JiraClient(
    base_url=JIRA_URL,
    username=JIRA_USERNAME,
    api_token=JIRA_API_TOKEN,
    mock_mode=JIRA_MOCK_MODE
)

# Create MCP server
mcp_server = Server("nexus-jira-agent")

# =============================================================================
# MCP Tool Definitions
# =============================================================================

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available Jira tools."""
    return [
        Tool(
            name="get_jira_issue",
            description="Fetch a single Jira ticket by its key (e.g., PROJ-123). Returns all ticket details including status, assignee, description, and metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Jira issue key (e.g., PROJ-123, NEXUS-456)"
                    }
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="search_jira_issues",
            description="Search Jira issues using JQL (Jira Query Language). Examples: 'project = PROJ AND status = \"In Progress\"', 'assignee = currentUser() AND sprint in openSprints()'",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {
                        "type": "string",
                        "description": "JQL query string"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50
                    }
                },
                "required": ["jql"]
            }
        ),
        Tool(
            name="get_sprint_stats",
            description="Get sprint statistics for a Jira project including completion rates, story points, and blockers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "Jira project key (e.g., PROJ, NEXUS)"
                    },
                    "sprint_id": {
                        "type": "integer",
                        "description": "Optional specific sprint ID. If not provided, returns current sprint stats."
                    }
                },
                "required": ["project_key"]
            }
        ),
        Tool(
            name="get_epic_hierarchy",
            description="Get a complete hierarchy of an epic including all stories and subtasks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "epic_key": {
                        "type": "string",
                        "description": "Jira epic key (e.g., PROJ-100)"
                    }
                },
                "required": ["epic_key"]
            }
        ),
        Tool(
            name="update_jira_issue",
            description="Update fields on a Jira issue. Can update labels, fix versions, story points, and add comments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Jira issue key"
                    },
                    "fields": {
                        "type": "object",
                        "description": "Fields to update (e.g., {\"labels\": [\"urgent\"], \"fixVersions\": [\"v2.0\"]})"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional comment to add to the issue"
                    }
                },
                "required": ["key"]
            }
        ),
        Tool(
            name="transition_jira_issue",
            description="Move a Jira issue to a new status (e.g., 'In Progress', 'Done', 'In Review').",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Jira issue key"
                    },
                    "transition": {
                        "type": "string",
                        "description": "Target status name (e.g., 'In Progress', 'Done')"
                    }
                },
                "required": ["key", "transition"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a Jira tool."""
    logger.info(f"Tool call: {name} with args: {arguments}")
    
    try:
        if name == "get_jira_issue":
            result = await jira_client.get_issue(arguments["key"])
        
        elif name == "search_jira_issues":
            result = await jira_client.search_issues(
                jql=arguments["jql"],
                max_results=arguments.get("max_results", 50)
            )
        
        elif name == "get_sprint_stats":
            result = await jira_client.get_sprint_stats(
                project_key=arguments["project_key"],
                sprint_id=arguments.get("sprint_id")
            )
        
        elif name == "get_epic_hierarchy":
            result = await jira_client.get_hierarchy(arguments["epic_key"])
        
        elif name == "update_jira_issue":
            result = await jira_client.update_issue(
                key=arguments["key"],
                fields=arguments.get("fields", {}),
                comment=arguments.get("comment")
            )
        
        elif name == "transition_jira_issue":
            result = await jira_client.transition_issue(
                key=arguments["key"],
                transition_name=arguments["transition"]
            )
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

# =============================================================================
# Starlette App with SSE Transport
# =============================================================================

async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "nexus-jira-agent",
        "version": "2.0.0",
        "transport": "mcp-sse",
        "mock_mode": JIRA_MOCK_MODE,
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
    """Legacy REST endpoint for backward compatibility with orchestrator."""
    try:
        body = await request.json()
        action = body.get("action", "")
        payload = body.get("payload", {})
        
        # Map legacy actions to MCP tools
        action_map = {
            "get_issue": ("get_jira_issue", {"key": payload.get("key")}),
            "search": ("search_jira_issues", {"jql": payload.get("jql"), "max_results": payload.get("max_results", 50)}),
            "get_sprint_stats": ("get_sprint_stats", {"project_key": payload.get("project_key"), "sprint_id": payload.get("sprint_id")}),
            "get_hierarchy": ("get_epic_hierarchy", {"epic_key": payload.get("epic_key")}),
            "update": ("update_jira_issue", {"key": payload.get("key"), "fields": payload.get("fields", {}), "comment": payload.get("comment")}),
            "transition": ("transition_jira_issue", {"key": payload.get("key"), "transition": payload.get("transition")})
        }
        
        if action not in action_map:
            return JSONResponse({"error": f"Unknown action: {action}"}, status_code=400)
        
        tool_name, tool_args = action_map[action]
        result = await call_tool(tool_name, tool_args)
        
        return JSONResponse({
            "status": "success",
            "data": json.loads(result[0].text) if result else {},
            "agent_type": "jira"
        })
    
    except Exception as e:
        logger.error(f"Execute error: {e}")
        return JSONResponse({
            "status": "failed",
            "error_message": str(e),
            "agent_type": "jira"
        }, status_code=500)

# Create Starlette app
app = Starlette(
    debug=os.getenv("NEXUS_ENV", "development") == "development",
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/sse", sse_endpoint, methods=["GET"]),
        Route("/execute", legacy_execute, methods=["POST"]),
        Route("/", health_check, methods=["GET"]),
    ],
    on_shutdown=[jira_client.close]
)

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info(f"🚀 Starting Nexus Jira Agent (MCP over SSE) on port {PORT}")
    logger.info(f"📡 Mock mode: {JIRA_MOCK_MODE}")
    logger.info(f"🔗 Jira URL: {JIRA_URL}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
