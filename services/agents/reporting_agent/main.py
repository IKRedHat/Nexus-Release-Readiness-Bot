"""
Nexus Reporting Agent
Generates rich HTML release reports and publishes to Confluence
"""
import os
import sys
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared")))

from nexus_lib.schemas.agent_contract import (
    AgentTaskRequest,
    AgentTaskResponse,
    ReleaseStats,
    ReleaseReport,
    ReleaseChecklist,
    ReleaseDecision,
    BuildResult,
    TaskStatus,
    AgentType,
)
from nexus_lib.middleware import MetricsMiddleware, AuthMiddleware
from nexus_lib.instrumentation import (
    setup_tracing,
    track_tool_usage,
    create_metrics_endpoint,
    REPORTS_GENERATED,
    RELEASE_DECISIONS,
)
from nexus_lib.utils import generate_task_id, utc_now

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nexus.reporting-agent")


# ============================================================================
# CONFLUENCE CLIENT WRAPPER
# ============================================================================

class ConfluenceClient:
    """
    Wrapper for Confluence API interactions using atlassian-python-api
    """
    
    def __init__(self):
        self.mock_mode = os.environ.get("CONFLUENCE_MOCK_MODE", "true").lower() == "true"
        self.confluence = None
        
        if not self.mock_mode:
            try:
                from atlassian import Confluence
                
                self.confluence = Confluence(
                    url=os.environ.get("CONFLUENCE_URL", "https://confluence.example.com"),
                    username=os.environ.get("CONFLUENCE_USERNAME"),
                    password=os.environ.get("CONFLUENCE_API_TOKEN"),
                    cloud=os.environ.get("CONFLUENCE_CLOUD", "true").lower() == "true"
                )
                logger.info("Confluence client initialized in LIVE mode")
            except ImportError:
                logger.warning("atlassian-python-api not installed, falling back to mock mode")
                self.mock_mode = True
            except Exception as e:
                logger.error(f"Failed to initialize Confluence client: {e}")
                self.mock_mode = True
        
        if self.mock_mode:
            logger.info("Confluence client running in MOCK mode")
    
    def create_page(
        self,
        space_key: str,
        title: str,
        body: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new Confluence page"""
        if self.mock_mode:
            logger.info(f"[MOCK] Created page: {title} in space {space_key}")
            return {
                "id": "mock-page-123",
                "title": title,
                "url": f"https://confluence.example.com/display/{space_key}/{title.replace(' ', '+')}"
            }
        
        try:
            result = self.confluence.create_page(
                space=space_key,
                title=title,
                body=body,
                parent_id=parent_id
            )
            return {
                "id": result["id"],
                "title": result["title"],
                "url": result["_links"]["base"] + result["_links"]["webui"]
            }
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            raise
    
    def update_page(
        self,
        page_id: str,
        title: str,
        body: str
    ) -> Dict[str, Any]:
        """Update an existing Confluence page"""
        if self.mock_mode:
            logger.info(f"[MOCK] Updated page: {page_id} - {title}")
            return {
                "id": page_id,
                "title": title,
                "url": f"https://confluence.example.com/pages/viewpage.action?pageId={page_id}"
            }
        
        try:
            result = self.confluence.update_page(
                page_id=page_id,
                title=title,
                body=body
            )
            return {
                "id": result["id"],
                "title": result["title"],
                "url": result["_links"]["base"] + result["_links"]["webui"]
            }
        except Exception as e:
            logger.error(f"Failed to update page: {e}")
            raise
    
    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get page content"""
        if self.mock_mode:
            return {
                "id": page_id,
                "title": "Mock Page",
                "body": "<p>Mock content</p>"
            }
        
        try:
            return self.confluence.get_page_by_id(page_id, expand="body.storage")
        except Exception as e:
            logger.error(f"Failed to get page: {e}")
            return None


# ============================================================================
# REPORT TEMPLATE ENGINE
# ============================================================================

class ReportGenerator:
    """
    Jinja2 template engine for generating release reports
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        if template_dir is None:
            template_dir = os.path.join(os.path.dirname(__file__), "templates")
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['status_color'] = self._status_color
        self.env.filters['decision_color'] = self._decision_color
        self.env.filters['severity_color'] = self._severity_color
        self.env.filters['percentage'] = self._format_percentage
        self.env.filters['datetime'] = self._format_datetime
        
        logger.info(f"Report generator initialized with templates from: {template_dir}")
    
    def _status_color(self, status: str) -> str:
        """Get color for status values"""
        colors = {
            "success": "#28a745",
            "done": "#28a745",
            "passed": "#28a745",
            "failure": "#dc3545",
            "failed": "#dc3545",
            "error": "#dc3545",
            "blocked": "#dc3545",
            "in_progress": "#ffc107",
            "in progress": "#ffc107",
            "pending": "#6c757d",
            "unstable": "#fd7e14",
            "warning": "#fd7e14"
        }
        return colors.get(status.lower(), "#6c757d")
    
    def _decision_color(self, decision: str) -> str:
        """Get color for Go/No-Go decisions"""
        colors = {
            "GO": "#28a745",
            "NO_GO": "#dc3545",
            "CONDITIONAL": "#fd7e14",
            "PENDING": "#6c757d"
        }
        return colors.get(decision, "#6c757d")
    
    def _severity_color(self, severity: str) -> str:
        """Get color for severity levels"""
        colors = {
            "critical": "#721c24",
            "high": "#dc3545",
            "medium": "#fd7e14",
            "low": "#ffc107",
            "info": "#17a2b8"
        }
        return colors.get(severity.lower(), "#6c757d")
    
    def _format_percentage(self, value: float) -> str:
        """Format percentage value"""
        return f"{value:.1f}%"
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for display"""
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            except:
                return dt
        return dt.strftime("%Y-%m-%d %H:%M UTC") if dt else "N/A"
    
    def generate_release_report(self, report_data: Dict[str, Any]) -> str:
        """Generate release readiness report HTML"""
        template = self.env.get_template("release_report.html")
        return template.render(report=report_data, generated_at=datetime.now())
    
    def generate_sprint_report(self, sprint_data: Dict[str, Any]) -> str:
        """Generate sprint summary report HTML"""
        template = self.env.get_template("sprint_report.html")
        return template.render(sprint=sprint_data, generated_at=datetime.now())
    
    def generate_security_report(self, security_data: Dict[str, Any]) -> str:
        """Generate security scan report HTML"""
        template = self.env.get_template("security_report.html")
        return template.render(security=security_data, generated_at=datetime.now())


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

confluence_client: Optional[ConfluenceClient] = None
report_generator: Optional[ReportGenerator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global confluence_client, report_generator
    
    # Startup
    setup_tracing("reporting-agent", service_version="1.0.0")
    confluence_client = ConfluenceClient()
    report_generator = ReportGenerator()
    logger.info("Reporting Agent started")
    
    yield
    
    # Shutdown
    logger.info("Reporting Agent shutting down")


app = FastAPI(
    title="Nexus Reporting Agent",
    description="Agent for generating and publishing release reports",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(MetricsMiddleware, agent_type="reporting")
app.add_middleware(
    AuthMiddleware,
    secret_key=os.environ.get("NEXUS_JWT_SECRET"),
    require_auth=os.environ.get("NEXUS_REQUIRE_AUTH", "false").lower() == "true"
)

# Add metrics endpoint
create_metrics_endpoint(app)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "reporting-agent",
        "confluence_mock": confluence_client.mock_mode if confluence_client else True
    }


@app.post("/generate", response_model=AgentTaskResponse)
@track_tool_usage("generate_report", agent_type="reporting")
async def generate_report(report_data: Dict[str, Any]):
    """
    Generate a release readiness report
    """
    task_id = generate_task_id("report")
    
    try:
        html_content = report_generator.generate_release_report(report_data)
        
        REPORTS_GENERATED.labels(report_type="release", destination="generated").inc()
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data={
                "html": html_content,
                "format": "html",
                "size_bytes": len(html_content.encode())
            },
            agent_type=AgentType.REPORTING
        )
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.REPORTING
        )


@app.get("/preview", response_class=HTMLResponse)
async def preview_report(
    release_version: str = Query("v2.0.0"),
    decision: str = Query("GO")
):
    """
    Preview a sample report (for demo purposes)
    """
    sample_data = {
        "stats": {
            "release_version": release_version,
            "release_date": datetime.now().isoformat(),
            "total_tickets": 45,
            "completed_tickets": 42,
            "in_progress_tickets": 2,
            "blocked_tickets": 1,
            "ticket_completion_rate": 93.3,
            "total_story_points": 89.0,
            "completed_story_points": 82.0,
            "test_coverage_percentage": 85.5,
            "passing_tests": 1245,
            "failing_tests": 3,
            "security_risk_score": 25,
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 2,
            "last_build_status": "SUCCESS",
            "build_success_rate": 95.5,
            "go_no_go": decision,
            "decision_rationale": "All critical criteria met. Minor issues documented but non-blocking.",
            "blockers": ["PROJ-105: API timeout issue"] if decision == "NO_GO" else [],
            "risks": [
                "2 high-severity vulnerabilities require patching within 7 days",
                "1 ticket still in progress"
            ],
            "checklist": [
                {"item": "All critical tickets completed", "passed": True, "required": True},
                {"item": "Test coverage > 80%", "passed": True, "required": True},
                {"item": "No critical vulnerabilities", "passed": True, "required": True},
                {"item": "CI pipeline green", "passed": True, "required": True},
                {"item": "Documentation updated", "passed": True, "required": False},
                {"item": "Performance benchmarks passed", "passed": True, "required": True},
            ]
        },
        "builds": [
            {
                "job_name": "nexus-main",
                "build_number": 142,
                "status": "SUCCESS",
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": 485
            }
        ],
        "security_scans": [
            {
                "repo_name": "nexus/backend",
                "risk_score": 25,
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 2
            }
        ]
    }
    
    html = report_generator.generate_release_report(sample_data)
    return HTMLResponse(content=html)


@app.post("/publish", response_model=AgentTaskResponse)
@track_tool_usage("publish_confluence_report", agent_type="reporting")
async def publish_report(
    page_id: Optional[str] = Query(None, description="Existing page ID to update"),
    space_key: str = Query("REL", description="Confluence space key"),
    title: str = Query(..., description="Page title"),
    report_data: Dict[str, Any] = None
):
    """
    Generate and publish report to Confluence
    """
    task_id = generate_task_id("publish")
    
    try:
        # Generate HTML
        html_content = report_generator.generate_release_report(report_data)
        
        # Publish to Confluence
        if page_id:
            result = confluence_client.update_page(page_id, title, html_content)
        else:
            result = confluence_client.create_page(space_key, title, html_content)
        
        # Track metrics
        decision = report_data.get("stats", {}).get("go_no_go", "PENDING")
        version = report_data.get("stats", {}).get("release_version", "unknown")
        
        REPORTS_GENERATED.labels(report_type="release", destination="confluence").inc()
        RELEASE_DECISIONS.labels(decision=decision, release_version=version).inc()
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data={
                "page_id": result["id"],
                "title": result["title"],
                "url": result["url"],
                "decision": decision
            },
            agent_type=AgentType.REPORTING
        )
    except Exception as e:
        logger.error(f"Failed to publish report: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.REPORTING
        )


@app.post("/analyze", response_model=AgentTaskResponse)
@track_tool_usage("analyze_release_readiness", agent_type="reporting")
async def analyze_readiness(report_data: Dict[str, Any]):
    """
    Analyze release data and determine Go/No-Go decision
    """
    task_id = generate_task_id("analyze")
    
    try:
        stats = report_data.get("stats", {})
        
        # Decision criteria
        checklist = []
        blockers = []
        risks = []
        
        # Check ticket completion
        completion_rate = stats.get("ticket_completion_rate", 0)
        tickets_ok = completion_rate >= 90
        checklist.append(ReleaseChecklist(
            item="Ticket completion rate >= 90%",
            passed=tickets_ok,
            details=f"Current: {completion_rate:.1f}%",
            required=True
        ))
        if not tickets_ok:
            blockers.append(f"Ticket completion only at {completion_rate:.1f}%")
        
        # Check blocked tickets
        blocked = stats.get("blocked_tickets", 0)
        no_blockers = blocked == 0
        checklist.append(ReleaseChecklist(
            item="No blocked tickets",
            passed=no_blockers,
            details=f"{blocked} blocked",
            required=True
        ))
        if not no_blockers:
            blockers.append(f"{blocked} tickets are blocked")
        
        # Check test coverage
        coverage = stats.get("test_coverage_percentage", 0)
        coverage_ok = coverage >= 80
        checklist.append(ReleaseChecklist(
            item="Test coverage >= 80%",
            passed=coverage_ok,
            details=f"Current: {coverage:.1f}%",
            required=True
        ))
        if not coverage_ok:
            risks.append(f"Test coverage at {coverage:.1f}%")
        
        # Check failing tests
        failing = stats.get("failing_tests", 0)
        tests_ok = failing == 0
        checklist.append(ReleaseChecklist(
            item="No failing tests",
            passed=tests_ok,
            details=f"{failing} failing",
            required=True
        ))
        if not tests_ok:
            blockers.append(f"{failing} tests are failing")
        
        # Check critical vulnerabilities
        critical_vulns = stats.get("critical_vulnerabilities", 0)
        security_ok = critical_vulns == 0
        checklist.append(ReleaseChecklist(
            item="No critical vulnerabilities",
            passed=security_ok,
            details=f"{critical_vulns} critical",
            required=True
        ))
        if not security_ok:
            blockers.append(f"{critical_vulns} critical vulnerabilities")
        
        # Check high vulnerabilities (warning only)
        high_vulns = stats.get("high_vulnerabilities", 0)
        if high_vulns > 0:
            risks.append(f"{high_vulns} high-severity vulnerabilities need attention")
        
        # Check build status
        build_status = stats.get("last_build_status", "UNKNOWN")
        build_ok = build_status in ["SUCCESS", "success"]
        checklist.append(ReleaseChecklist(
            item="Last build successful",
            passed=build_ok,
            details=f"Status: {build_status}",
            required=True
        ))
        if not build_ok:
            blockers.append(f"Last build status: {build_status}")
        
        # Determine decision
        required_passed = all(c.passed for c in checklist if c.required)
        
        if required_passed and len(blockers) == 0:
            decision = ReleaseDecision.GO
            rationale = "All required criteria met. Release is approved."
        elif len(blockers) == 0 and len(risks) > 0:
            decision = ReleaseDecision.CONDITIONAL
            rationale = "Release approved with conditions. Address risks within 7 days."
        else:
            decision = ReleaseDecision.NO_GO
            rationale = f"Release blocked due to {len(blockers)} critical issue(s)."
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data={
                "decision": decision.value,
                "rationale": rationale,
                "checklist": [c.model_dump() for c in checklist],
                "blockers": blockers,
                "risks": risks,
                "required_criteria_passed": required_passed
            },
            agent_type=AgentType.REPORTING
        )
    except Exception as e:
        logger.error(f"Failed to analyze readiness: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.REPORTING
        )


@app.post("/execute", response_model=AgentTaskResponse)
async def execute_task(request: AgentTaskRequest):
    """
    Generic task execution endpoint for orchestrator integration
    """
    action = request.action
    payload = request.payload
    
    # Route to appropriate handler
    if action == "generate":
        return await generate_report(payload)
    elif action == "publish":
        return await publish_report(
            page_id=payload.get("page_id"),
            space_key=payload.get("space_key", "REL"),
            title=payload.get("title"),
            report_data=payload.get("report_data")
        )
    elif action == "analyze":
        return await analyze_readiness(payload)
    else:
        return AgentTaskResponse(
            task_id=request.task_id,
            status=TaskStatus.FAILED,
            error_message=f"Unknown action: {action}",
            agent_type=AgentType.REPORTING
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
