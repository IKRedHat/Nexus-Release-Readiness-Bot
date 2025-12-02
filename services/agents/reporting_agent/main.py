"""
Nexus Reporting Agent - MCP Server Implementation
==================================================

Report generation and Confluence publishing agent exposed via MCP over SSE.
Provides tools for generating release reports, publishing to Confluence, and analyzing release readiness.

Architecture: MCP Server with SSE Transport
Port: 8083
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import random

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse, HTMLResponse
from starlette.requests import Request
from jinja2 import Environment, FileSystemLoader, select_autoescape
import uvicorn
import httpx

# Add shared lib path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', 'shared'))

try:
    from nexus_lib.config import ConfigManager, ConfigKeys
    from nexus_lib.schemas.agent_contract import (
        ReleaseStats, ReleaseReport, ReleaseDecision, ReleaseChecklist
    )
except ImportError:
    ConfigManager = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("nexus.reporting-agent")

# =============================================================================
# Configuration
# =============================================================================

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "https://your-org.atlassian.net/wiki")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY", "REL")
CONFLUENCE_MOCK_MODE = os.getenv("CONFLUENCE_MOCK_MODE", "true").lower() == "true"
PORT = int(os.getenv("REPORTING_AGENT_PORT", "8083"))

# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Initialize Jinja2 environment
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR) if os.path.exists(TEMPLATE_DIR) else None,
    autoescape=select_autoescape(["html", "xml"])
)

# =============================================================================
# Report Templates
# =============================================================================

RELEASE_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Release Readiness Report - {{ release_version }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 30px; }
        h1 { color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; }
        h2 { color: #333; margin-top: 30px; }
        .decision { padding: 15px; border-radius: 8px; margin: 20px 0; font-size: 24px; font-weight: bold; text-align: center; }
        .decision.GO { background: #d4edda; color: #155724; border: 2px solid #28a745; }
        .decision.NO_GO { background: #f8d7da; color: #721c24; border: 2px solid #dc3545; }
        .decision.CONDITIONAL { background: #fff3cd; color: #856404; border: 2px solid #ffc107; }
        .decision.PENDING { background: #e2e3e5; color: #383d41; border: 2px solid #6c757d; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .metric-value { font-size: 28px; font-weight: bold; color: #1a73e8; }
        .metric-label { color: #666; font-size: 14px; margin-top: 5px; }
        .progress-bar { background: #e9ecef; border-radius: 4px; height: 20px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #1a73e8, #34a853); transition: width 0.3s; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
        .status-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
        .status-passed { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-warning { background: #fff3cd; color: #856404; }
        .blockers { background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0; }
        .risks { background: #f8d7da; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Release Readiness Report</h1>
        <p><strong>Version:</strong> {{ release_version }} | <strong>Generated:</strong> {{ generated_at }}</p>
        
        <div class="decision {{ go_no_go }}">
            {{ go_no_go }} - {{ decision_rationale }}
        </div>
        
        <h2>📊 Key Metrics</h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{{ ticket_completion_rate }}%</div>
                <div class="metric-label">Ticket Completion</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ completed_tickets }}/{{ total_tickets }}</div>
                <div class="metric-label">Tickets Done</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ security_risk_score }}</div>
                <div class="metric-label">Security Score</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ test_coverage }}%</div>
                <div class="metric-label">Test Coverage</div>
            </div>
        </div>
        
        <h2>📈 Sprint Progress</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ ticket_completion_rate }}%"></div>
        </div>
        <p>{{ completed_story_points }} / {{ total_story_points }} story points completed</p>
        
        {% if blockers %}
        <div class="blockers">
            <h3>⚠️ Blockers ({{ blockers|length }})</h3>
            <ul>
            {% for blocker in blockers %}
                <li>{{ blocker }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        {% if risks %}
        <div class="risks">
            <h3>🔴 Risks ({{ risks|length }})</h3>
            <ul>
            {% for risk in risks %}
                <li>{{ risk }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        <h2>✅ Release Checklist</h2>
        <table>
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
            {% for item in checklist %}
                <tr>
                    <td>{{ item.item }}</td>
                    <td>
                        <span class="status-badge {% if item.passed %}status-passed{% else %}status-failed{% endif %}">
                            {% if item.passed %}✓ Passed{% else %}✗ Failed{% endif %}
                        </span>
                    </td>
                    <td>{{ item.details or '-' }}</td>
                </tr>
            {% endfor %}
            </tbody>
        </table>
        
        <h2>🔒 Security Summary</h2>
        <table>
            <tr>
                <th>Severity</th>
                <th>Count</th>
            </tr>
            <tr>
                <td>Critical</td>
                <td>{{ critical_vulnerabilities }}</td>
            </tr>
            <tr>
                <td>High</td>
                <td>{{ high_vulnerabilities }}</td>
            </tr>
        </table>
        
        <h2>🏗️ Build Status</h2>
        <p><strong>Last Build:</strong> {{ last_build_status }}</p>
        <p><strong>Success Rate:</strong> {{ build_success_rate }}%</p>
        <p><strong>Passing Tests:</strong> {{ passing_tests }} | <strong>Failing Tests:</strong> {{ failing_tests }}</p>
        
        <div class="footer">
            <p>Generated by Nexus Release Automation System</p>
            <p>Report ID: {{ report_id }}</p>
        </div>
    </div>
</body>
</html>
"""

# =============================================================================
# Mock Data Generator
# =============================================================================

class MockReportData:
    """Generates realistic mock report data."""
    
    @classmethod
    def generate_release_stats(cls, version: str) -> Dict[str, Any]:
        """Generate mock release statistics."""
        total_tickets = random.randint(30, 80)
        completed = random.randint(int(total_tickets * 0.7), total_tickets)
        in_progress = random.randint(0, total_tickets - completed)
        blocked = total_tickets - completed - in_progress
        
        total_points = random.uniform(50, 150)
        completed_points = total_points * (completed / total_tickets)
        
        completion_rate = round((completed / total_tickets) * 100, 1)
        
        # Determine go/no-go based on metrics
        if completion_rate >= 95 and blocked == 0:
            decision = "GO"
            rationale = "All metrics meet release criteria"
        elif completion_rate >= 80 and blocked <= 2:
            decision = "CONDITIONAL"
            rationale = f"Release approved with {blocked} known blockers"
        else:
            decision = "NO_GO"
            rationale = f"Only {completion_rate}% complete with {blocked} blockers"
        
        return {
            "release_version": version,
            "release_date": datetime.utcnow().isoformat(),
            "total_tickets": total_tickets,
            "completed_tickets": completed,
            "in_progress_tickets": in_progress,
            "blocked_tickets": blocked,
            "ticket_completion_rate": completion_rate,
            "total_story_points": round(total_points, 1),
            "completed_story_points": round(completed_points, 1),
            "test_coverage_percentage": round(random.uniform(75, 95), 1),
            "passing_tests": random.randint(200, 500),
            "failing_tests": random.randint(0, 10),
            "security_risk_score": random.randint(15, 45),
            "critical_vulnerabilities": random.choice([0, 0, 0, 1]),
            "high_vulnerabilities": random.randint(0, 5),
            "last_build_status": random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "FAILURE"]),
            "build_success_rate": round(random.uniform(85, 100), 1),
            "go_no_go": decision,
            "decision_rationale": rationale,
            "blockers": [f"PROJ-{random.randint(100, 999)}: {reason}" for reason in ["Dependency update needed", "API contract change", "Performance regression"][:blocked]],
            "risks": [
                "Third-party API deprecation in Q1",
                "Database migration complexity"
            ] if random.random() > 0.5 else [],
            "checklist": [
                {"item": "All tests passing", "passed": random.choice([True, True, False]), "details": "CI/CD pipeline status", "required": True},
                {"item": "Security scan completed", "passed": True, "details": "No critical vulnerabilities", "required": True},
                {"item": "Documentation updated", "passed": random.choice([True, False]), "details": "API docs and changelog", "required": True},
                {"item": "Performance testing", "passed": True, "details": "Load tests passed", "required": True},
                {"item": "Stakeholder approval", "passed": random.choice([True, True, False]), "details": "Sign-off from product", "required": True},
            ]
        }

# =============================================================================
# Confluence Client
# =============================================================================

class ConfluenceClient:
    """Confluence REST API client with mock fallback."""
    
    def __init__(self, base_url: str, username: str, api_token: str, space_key: str, mock_mode: bool = False):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.api_token = api_token
        self.space_key = space_key
        self.mock_mode = mock_mode
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            auth = (self.username, self.api_token) if self.username and self.api_token else None
            self._client = httpx.AsyncClient(
                base_url=f"{self.base_url}/rest/api",
                auth=auth,
                timeout=30.0,
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def create_page(self, title: str, content: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Confluence page."""
        if self.mock_mode:
            page_id = str(random.randint(100000, 999999))
            return {
                "id": page_id,
                "title": title,
                "url": f"{self.base_url}/spaces/{self.space_key}/pages/{page_id}",
                "space_key": self.space_key,
                "created": True
            }
        
        client = await self._get_client()
        
        # Convert HTML to Confluence storage format
        body = {
            "type": "page",
            "title": title,
            "space": {"key": self.space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        
        if parent_id:
            body["ancestors"] = [{"id": parent_id}]
        
        response = await client.post("/content", json=body)
        response.raise_for_status()
        data = response.json()
        
        return {
            "id": data["id"],
            "title": data["title"],
            "url": f"{self.base_url}{data['_links']['webui']}",
            "space_key": self.space_key,
            "created": True
        }
    
    async def update_page(self, page_id: str, title: str, content: str, version: int) -> Dict[str, Any]:
        """Update an existing Confluence page."""
        if self.mock_mode:
            return {
                "id": page_id,
                "title": title,
                "url": f"{self.base_url}/spaces/{self.space_key}/pages/{page_id}",
                "space_key": self.space_key,
                "updated": True,
                "version": version + 1
            }
        
        client = await self._get_client()
        
        body = {
            "type": "page",
            "title": title,
            "version": {"number": version + 1},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        
        response = await client.put(f"/content/{page_id}", json=body)
        response.raise_for_status()
        data = response.json()
        
        return {
            "id": data["id"],
            "title": data["title"],
            "url": f"{self.base_url}{data['_links']['webui']}",
            "updated": True,
            "version": data["version"]["number"]
        }
    
    async def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a Confluence page by ID."""
        if self.mock_mode:
            return {
                "id": page_id,
                "title": f"Release Report - Mock",
                "version": {"number": random.randint(1, 10)},
                "url": f"{self.base_url}/spaces/{self.space_key}/pages/{page_id}"
            }
        
        client = await self._get_client()
        response = await client.get(f"/content/{page_id}")
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        return response.json()

# =============================================================================
# Report Generator
# =============================================================================

class ReportGenerator:
    """Generates HTML reports from release data."""
    
    def __init__(self):
        self.template = jinja_env.from_string(RELEASE_REPORT_TEMPLATE)
    
    def generate_html(self, stats: Dict[str, Any]) -> str:
        """Generate HTML report from release stats."""
        context = {
            "release_version": stats.get("release_version", "Unknown"),
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "report_id": f"REP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "go_no_go": stats.get("go_no_go", "PENDING"),
            "decision_rationale": stats.get("decision_rationale", "Awaiting analysis"),
            "ticket_completion_rate": stats.get("ticket_completion_rate", 0),
            "completed_tickets": stats.get("completed_tickets", 0),
            "total_tickets": stats.get("total_tickets", 0),
            "completed_story_points": stats.get("completed_story_points", 0),
            "total_story_points": stats.get("total_story_points", 0),
            "security_risk_score": stats.get("security_risk_score", 0),
            "test_coverage": stats.get("test_coverage_percentage", 0),
            "critical_vulnerabilities": stats.get("critical_vulnerabilities", 0),
            "high_vulnerabilities": stats.get("high_vulnerabilities", 0),
            "last_build_status": stats.get("last_build_status", "UNKNOWN"),
            "build_success_rate": stats.get("build_success_rate", 0),
            "passing_tests": stats.get("passing_tests", 0),
            "failing_tests": stats.get("failing_tests", 0),
            "blockers": stats.get("blockers", []),
            "risks": stats.get("risks", []),
            "checklist": stats.get("checklist", [])
        }
        
        return self.template.render(**context)
    
    def analyze_readiness(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze release readiness and generate decision."""
        completion_rate = stats.get("ticket_completion_rate", 0)
        blocked = stats.get("blocked_tickets", 0)
        critical_vulns = stats.get("critical_vulnerabilities", 0)
        failing_tests = stats.get("failing_tests", 0)
        
        # Decision logic
        issues = []
        
        if completion_rate < 80:
            issues.append(f"Low completion rate: {completion_rate}%")
        
        if blocked > 0:
            issues.append(f"{blocked} blocked ticket(s)")
        
        if critical_vulns > 0:
            issues.append(f"{critical_vulns} critical vulnerability(ies)")
        
        if failing_tests > 0:
            issues.append(f"{failing_tests} failing test(s)")
        
        # Determine decision
        if not issues:
            decision = "GO"
            confidence = 0.95
            rationale = "All release criteria met"
        elif len(issues) == 1 and blocked <= 2 and critical_vulns == 0:
            decision = "CONDITIONAL"
            confidence = 0.75
            rationale = f"Release approved with minor issues: {issues[0]}"
        else:
            decision = "NO_GO"
            confidence = 0.85
            rationale = f"Release blocked: {', '.join(issues)}"
        
        return {
            "decision": decision,
            "confidence": confidence,
            "rationale": rationale,
            "issues": issues,
            "recommendations": [
                "Address all blockers before release",
                "Ensure security scan passes",
                "Complete remaining tickets"
            ] if decision != "GO" else ["Proceed with release deployment"]
        }

# =============================================================================
# Initialize Clients
# =============================================================================

confluence_client = ConfluenceClient(
    base_url=CONFLUENCE_URL,
    username=CONFLUENCE_USERNAME,
    api_token=CONFLUENCE_API_TOKEN,
    space_key=CONFLUENCE_SPACE_KEY,
    mock_mode=CONFLUENCE_MOCK_MODE
)

report_generator = ReportGenerator()

# Create MCP server
mcp_server = Server("nexus-reporting-agent")

# =============================================================================
# MCP Tool Definitions
# =============================================================================

@mcp_server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available reporting tools."""
    return [
        Tool(
            name="generate_release_report",
            description="Generate an HTML release readiness report from provided statistics or by fetching data for a version.",
            inputSchema={
                "type": "object",
                "properties": {
                    "version": {
                        "type": "string",
                        "description": "Release version (e.g., v2.0.0)"
                    },
                    "stats": {
                        "type": "object",
                        "description": "Optional pre-computed release statistics"
                    }
                },
                "required": ["version"]
            }
        ),
        Tool(
            name="analyze_release_readiness",
            description="Analyze release statistics and provide a Go/No-Go recommendation with confidence score.",
            inputSchema={
                "type": "object",
                "properties": {
                    "version": {
                        "type": "string",
                        "description": "Release version to analyze"
                    },
                    "stats": {
                        "type": "object",
                        "description": "Release statistics to analyze"
                    }
                },
                "required": ["version"]
            }
        ),
        Tool(
            name="publish_to_confluence",
            description="Publish a release report to Confluence. Creates a new page or updates an existing one.",
            inputSchema={
                "type": "object",
                "properties": {
                    "version": {
                        "type": "string",
                        "description": "Release version"
                    },
                    "html_content": {
                        "type": "string",
                        "description": "HTML content to publish"
                    },
                    "page_id": {
                        "type": "string",
                        "description": "Existing page ID to update (optional, creates new page if not provided)"
                    },
                    "parent_page_id": {
                        "type": "string",
                        "description": "Parent page ID for new pages"
                    }
                },
                "required": ["version", "html_content"]
            }
        ),
        Tool(
            name="get_release_stats",
            description="Get current release statistics for a version (mock data in development mode).",
            inputSchema={
                "type": "object",
                "properties": {
                    "version": {
                        "type": "string",
                        "description": "Release version"
                    }
                },
                "required": ["version"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a reporting tool."""
    logger.info(f"Tool call: {name} with args: {arguments}")
    
    try:
        if name == "generate_release_report":
            version = arguments["version"]
            stats = arguments.get("stats") or MockReportData.generate_release_stats(version)
            html = report_generator.generate_html(stats)
            
            result = {
                "version": version,
                "html_content": html,
                "stats": stats,
                "generated_at": datetime.utcnow().isoformat()
            }
        
        elif name == "analyze_release_readiness":
            version = arguments["version"]
            stats = arguments.get("stats") or MockReportData.generate_release_stats(version)
            analysis = report_generator.analyze_readiness(stats)
            
            result = {
                "version": version,
                **analysis,
                "stats_summary": {
                    "completion_rate": stats.get("ticket_completion_rate"),
                    "blocked": stats.get("blocked_tickets"),
                    "security_score": stats.get("security_risk_score")
                }
            }
        
        elif name == "publish_to_confluence":
            version = arguments["version"]
            html_content = arguments["html_content"]
            page_id = arguments.get("page_id")
            parent_page_id = arguments.get("parent_page_id")
            
            title = f"Release Readiness Report - {version}"
            
            if page_id:
                # Update existing page
                page = await confluence_client.get_page(page_id)
                if page:
                    result = await confluence_client.update_page(
                        page_id=page_id,
                        title=title,
                        content=html_content,
                        version=page["version"]["number"]
                    )
                else:
                    result = {"error": f"Page {page_id} not found"}
            else:
                # Create new page
                result = await confluence_client.create_page(
                    title=title,
                    content=html_content,
                    parent_id=parent_page_id
                )
        
        elif name == "get_release_stats":
            version = arguments["version"]
            result = MockReportData.generate_release_stats(version)
        
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
        "service": "nexus-reporting-agent",
        "version": "2.0.0",
        "transport": "mcp-sse",
        "confluence_mock_mode": CONFLUENCE_MOCK_MODE,
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

async def preview_report(request: Request) -> HTMLResponse:
    """Preview a sample release report."""
    version = request.query_params.get("version", "v2.0.0")
    stats = MockReportData.generate_release_stats(version)
    html = report_generator.generate_html(stats)
    return HTMLResponse(content=html)

async def legacy_execute(request: Request) -> JSONResponse:
    """Legacy REST endpoint for backward compatibility."""
    try:
        body = await request.json()
        action = body.get("action", "")
        payload = body.get("payload", {})
        
        action_map = {
            "generate": ("generate_release_report", {"version": payload.get("version"), "stats": payload.get("stats")}),
            "analyze": ("analyze_release_readiness", {"version": payload.get("version"), "stats": payload.get("stats")}),
            "publish": ("publish_to_confluence", {"version": payload.get("version"), "html_content": payload.get("html_content"), "page_id": payload.get("page_id")}),
            "get_stats": ("get_release_stats", {"version": payload.get("version")}),
        }
        
        if action not in action_map:
            return JSONResponse({"error": f"Unknown action: {action}"}, status_code=400)
        
        tool_name, tool_args = action_map[action]
        result = await call_tool(tool_name, tool_args)
        
        return JSONResponse({
            "status": "success",
            "data": json.loads(result[0].text) if result else {},
            "agent_type": "reporting"
        })
    
    except Exception as e:
        logger.error(f"Execute error: {e}")
        return JSONResponse({
            "status": "failed",
            "error_message": str(e),
            "agent_type": "reporting"
        }, status_code=500)

app = Starlette(
    debug=os.getenv("NEXUS_ENV", "development") == "development",
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/sse", sse_endpoint, methods=["GET"]),
        Route("/execute", legacy_execute, methods=["POST"]),
        Route("/preview", preview_report, methods=["GET"]),
        Route("/", health_check, methods=["GET"]),
    ],
    on_shutdown=[confluence_client.close]
)

# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    logger.info(f"🚀 Starting Nexus Reporting Agent (MCP over SSE) on port {PORT}")
    logger.info(f"📡 Confluence mock mode: {CONFLUENCE_MOCK_MODE}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
