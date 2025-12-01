"""
Nexus Jira Agent
Handles all Jira-related operations including ticket fetching, updates, and hierarchy traversal

Now with dynamic configuration via ConfigManager - supports live mode switching from Admin Dashboard.
"""
import os
import sys
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from prometheus_client import Counter

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared")))

from nexus_lib.schemas.agent_contract import (
    AgentTaskRequest,
    AgentTaskResponse,
    JiraTicket,
    JiraUser,
    JiraComment,
    JiraSearchResult,
    JiraSprintStats,
    JiraIssueType,
    TaskStatus,
    AgentType,
)
from nexus_lib.middleware import MetricsMiddleware, AuthMiddleware
from nexus_lib.instrumentation import (
    setup_tracing,
    track_tool_usage,
    create_metrics_endpoint,
    JIRA_TICKETS_PROCESSED,
)
from nexus_lib.utils import generate_task_id, utc_now
from nexus_lib.config import ConfigManager, ConfigKeys, is_mock_mode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nexus.jira-agent")


# ============================================================================
# JIRA CLIENT WRAPPER
# ============================================================================

class JiraClient:
    """
    Wrapper for Jira API interactions using atlassian-python-api
    Supports both real API calls and mock mode for development
    
    Now uses ConfigManager for dynamic configuration:
    - Mode can be switched live via Admin Dashboard
    - Credentials are fetched from Redis/env/defaults
    """
    
    def __init__(self):
        self._jira = None
        self._last_mode = None
        self._initialized = False
        logger.info("Jira client created - will initialize on first use")
    
    async def _ensure_initialized(self):
        """
        Lazy initialization - checks config on each operation.
        This allows live mode switching without restart.
        """
        current_mock_mode = await is_mock_mode()
        
        # Reinitialize if mode changed or not initialized
        if self._last_mode != current_mock_mode or not self._initialized:
            self._last_mode = current_mock_mode
            self._initialized = True
            
            if current_mock_mode:
                logger.info("Jira client operating in MOCK mode")
                self._jira = None
            else:
                await self._init_live_client()
    
    async def _init_live_client(self):
        """Initialize the live Jira client with credentials from ConfigManager."""
        try:
            from atlassian import Jira
            
            jira_url = await ConfigManager.get(ConfigKeys.JIRA_URL)
            jira_username = await ConfigManager.get(ConfigKeys.JIRA_USERNAME)
            jira_token = await ConfigManager.get(ConfigKeys.JIRA_API_TOKEN)
            
            if not all([jira_url, jira_username, jira_token]):
                logger.warning("Jira credentials incomplete, falling back to mock mode")
                self._last_mode = True
                self._jira = None
                return
            
            self._jira = Jira(
                url=jira_url,
                username=jira_username,
                password=jira_token,
                cloud=True  # Assume cloud by default
            )
            logger.info(f"Jira client initialized in LIVE mode - {jira_url}")
            
        except ImportError:
            logger.warning("atlassian-python-api not installed, using mock mode")
            self._last_mode = True
            self._jira = None
        except Exception as e:
            logger.error(f"Failed to initialize Jira client: {e}")
            self._last_mode = True
            self._jira = None
    
    @property
    def mock_mode(self) -> bool:
        """Check if currently in mock mode."""
        return self._last_mode if self._last_mode is not None else True
    
    def _parse_user(self, user_data: Optional[Dict]) -> Optional[JiraUser]:
        """Parse Jira user data into JiraUser model"""
        if not user_data:
            return None
        return JiraUser(
            account_id=user_data.get("accountId", "unknown"),
            display_name=user_data.get("displayName", "Unknown User"),
            email=user_data.get("emailAddress"),
            avatar_url=user_data.get("avatarUrls", {}).get("48x48"),
            active=user_data.get("active", True)
        )
    
    def _parse_issue(self, issue: Dict, include_subtasks: bool = False) -> JiraTicket:
        """Parse Jira issue data into JiraTicket model"""
        fields = issue.get("fields", {})
        
        # Parse basic fields
        ticket = JiraTicket(
            key=issue["key"],
            id=issue.get("id"),
            summary=fields.get("summary", "No summary"),
            description=fields.get("description"),
            issue_type=self._map_issue_type(fields.get("issuetype", {}).get("name")),
            status=fields.get("status", {}).get("name", "Unknown"),
            resolution=fields.get("resolution", {}).get("name") if fields.get("resolution") else None,
            priority=fields.get("priority", {}).get("name", "Medium"),
            project_key=fields.get("project", {}).get("key"),
            parent_key=fields.get("parent", {}).get("key"),
            epic_key=fields.get("customfield_10014") or fields.get("epic", {}).get("key") if fields.get("epic") else None,
            assignee=self._parse_user(fields.get("assignee")),
            reporter=self._parse_user(fields.get("reporter")),
            story_points=fields.get("customfield_10016"),
            sprint_name=self._extract_sprint_name(fields),
            labels=fields.get("labels", []),
            components=[c.get("name") for c in fields.get("components", [])],
            fix_versions=[v.get("name") for v in fields.get("fixVersions", [])],
            created_at=self._parse_datetime(fields.get("created")),
            updated_at=self._parse_datetime(fields.get("updated")),
            resolved_at=self._parse_datetime(fields.get("resolutiondate")),
            due_date=self._parse_datetime(fields.get("duedate")),
        )
        
        # Parse subtasks if requested
        if include_subtasks and fields.get("subtasks"):
            ticket.subtasks = [
                JiraTicket(
                    key=st["key"],
                    summary=st["fields"]["summary"],
                    status=st["fields"]["status"]["name"],
                    issue_type=JiraIssueType.SUBTASK
                )
                for st in fields["subtasks"]
            ]
        
        return ticket
    
    def _map_issue_type(self, type_name: str) -> JiraIssueType:
        """Map Jira issue type name to enum"""
        type_mapping = {
            "Epic": JiraIssueType.EPIC,
            "Story": JiraIssueType.STORY,
            "Task": JiraIssueType.TASK,
            "Sub-task": JiraIssueType.SUBTASK,
            "Bug": JiraIssueType.BUG,
            "Spike": JiraIssueType.SPIKE,
        }
        return type_mapping.get(type_name, JiraIssueType.TASK)
    
    def _extract_sprint_name(self, fields: Dict) -> Optional[str]:
        """Extract sprint name from Jira fields"""
        sprints = fields.get("customfield_10020", [])
        if sprints and len(sprints) > 0:
            sprint = sprints[-1]
            if isinstance(sprint, str):
                if "name=" in sprint:
                    start = sprint.find("name=") + 5
                    end = sprint.find(",", start)
                    return sprint[start:end] if end > start else sprint[start:]
            elif isinstance(sprint, dict):
                return sprint.get("name")
        return None
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse Jira datetime string"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
    
    async def get_issue(self, key: str, expand: str = "changelog") -> JiraTicket:
        """Fetch a single Jira issue"""
        await self._ensure_initialized()
        
        if self.mock_mode:
            return self._mock_issue(key)
        
        issue = self._jira.issue(key, expand=expand)
        return self._parse_issue(issue, include_subtasks=True)
    
    async def get_issue_hierarchy(self, key: str, max_depth: int = 3) -> JiraTicket:
        """Recursively fetch issue hierarchy (Epic -> Stories -> Subtasks)"""
        await self._ensure_initialized()
        
        if self.mock_mode:
            return self._mock_hierarchy(key)
        
        root = await self.get_issue(key)
        await self._fetch_children(root, depth=0, max_depth=max_depth)
        return root
    
    async def _fetch_children(self, ticket: JiraTicket, depth: int, max_depth: int):
        """Recursively fetch child issues"""
        if depth >= max_depth:
            return
        
        if ticket.issue_type == JiraIssueType.EPIC:
            jql = f'"Epic Link" = {ticket.key}'
            results = await self.search_issues(jql)
            ticket.subtasks = results.issues
            
            for child in ticket.subtasks:
                await self._fetch_children(child, depth + 1, max_depth)
    
    async def search_issues(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 50,
        fields: str = "*all"
    ) -> JiraSearchResult:
        """Search issues using JQL"""
        await self._ensure_initialized()
        
        if self.mock_mode:
            return self._mock_search(jql, max_results)
        
        result = self._jira.jql(jql, start=start_at, limit=max_results, fields=fields)
        
        return JiraSearchResult(
            total=result.get("total", 0),
            start_at=result.get("startAt", 0),
            max_results=result.get("maxResults", max_results),
            issues=[self._parse_issue(issue) for issue in result.get("issues", [])]
        )
    
    async def update_issue_status(self, key: str, status: str, comment: Optional[str] = None) -> bool:
        """Update issue status using transition"""
        await self._ensure_initialized()
        
        if self.mock_mode:
            logger.info(f"[MOCK] Updated {key} to status: {status}")
            return True
        
        try:
            transitions = self._jira.get_issue_transitions(key)
            
            target_transition = None
            for t in transitions.get("transitions", []):
                if t["to"]["name"].lower() == status.lower():
                    target_transition = t["id"]
                    break
            
            if not target_transition:
                logger.warning(f"No transition found for status: {status}")
                return False
            
            self._jira.set_issue_status(key, target_transition)
            
            if comment:
                self._jira.issue_add_comment(key, comment)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update issue status: {e}")
            return False
    
    async def update_issue_fields(self, key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update multiple fields on a Jira issue"""
        await self._ensure_initialized()
        
        if self.mock_mode:
            logger.info(f"[MOCK] Updated {key} with fields: {list(fields.keys())}")
            return {
                "success": True,
                "ticket_key": key,
                "fields_updated": list(fields.keys()),
                "mock": True
            }
        
        try:
            update_payload = {"fields": {}}
            for field_name, value in fields.items():
                update_payload["fields"][field_name] = value
            
            self._jira.update_issue_field(key, update_payload["fields"])
            
            logger.info(f"Updated {key} fields: {list(fields.keys())}")
            
            return {
                "success": True,
                "ticket_key": key,
                "fields_updated": list(fields.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to update issue fields on {key}: {e}")
            return {
                "success": False,
                "ticket_key": key,
                "error": str(e)
            }
    
    async def add_comment(self, key: str, comment: str) -> bool:
        """Add comment to an issue"""
        await self._ensure_initialized()
        
        if self.mock_mode:
            logger.info(f"[MOCK] Added comment to {key}: {comment[:50]}...")
            return True
        
        try:
            self._jira.issue_add_comment(key, comment)
            return True
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            return False
    
    async def get_sprint_stats(self, project_key: str, sprint_name: Optional[str] = None) -> JiraSprintStats:
        """Get sprint statistics for a project"""
        await self._ensure_initialized()
        
        if self.mock_mode:
            return self._mock_sprint_stats(project_key, sprint_name)
        
        jql = f'project = {project_key}'
        if sprint_name:
            jql += f' AND sprint = "{sprint_name}"'
        else:
            jql += ' AND sprint in openSprints()'
        
        result = await self.search_issues(jql, max_results=500)
        
        total = len(result.issues)
        completed = sum(1 for i in result.issues if i.status.lower() == "done")
        in_progress = sum(1 for i in result.issues if i.status.lower() == "in progress")
        blocked = sum(1 for i in result.issues if "block" in i.status.lower())
        
        total_points = sum(i.story_points or 0 for i in result.issues)
        completed_points = sum(i.story_points or 0 for i in result.issues if i.status.lower() == "done")
        
        blockers = [i.key for i in result.issues if "block" in i.status.lower()]
        
        return JiraSprintStats(
            sprint_id=0,
            sprint_name=sprint_name or "Current Sprint",
            total_issues=total,
            completed_issues=completed,
            in_progress_issues=in_progress,
            blocked_issues=blocked,
            total_story_points=total_points,
            completed_story_points=completed_points,
            completion_percentage=(completed / total * 100) if total > 0 else 0,
            blockers=blockers
        )
    
    # ============================================================================
    # MOCK DATA GENERATORS
    # ============================================================================
    
    def _mock_issue(self, key: str) -> JiraTicket:
        """Generate mock issue data"""
        project = key.split("-")[0] if "-" in key else "PROJ"
        return JiraTicket(
            key=key,
            id=f"10{key.split('-')[1] if '-' in key else '001'}",
            summary=f"[Demo] Implementation task for {key}",
            description="This is a mock Jira ticket for demonstration purposes.",
            issue_type=JiraIssueType.STORY,
            status="In Progress",
            priority="Medium",
            project_key=project,
            assignee=JiraUser(
                account_id="user-123",
                display_name="Demo User",
                email="demo@example.com"
            ),
            reporter=JiraUser(
                account_id="user-456",
                display_name="Project Manager",
                email="pm@example.com"
            ),
            story_points=5.0,
            sprint_name="Sprint 42",
            labels=["backend", "api"],
            components=["core"],
            fix_versions=["v2.0.0"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            subtasks=[
                JiraTicket(
                    key=f"{key}-1",
                    summary="Subtask: Write unit tests",
                    status="Done",
                    issue_type=JiraIssueType.SUBTASK
                ),
                JiraTicket(
                    key=f"{key}-2",
                    summary="Subtask: Code review",
                    status="In Progress",
                    issue_type=JiraIssueType.SUBTASK
                )
            ]
        )
    
    def _mock_hierarchy(self, key: str) -> JiraTicket:
        """Generate mock epic hierarchy"""
        project = key.split("-")[0] if "-" in key else "PROJ"
        return JiraTicket(
            key=key,
            summary=f"[Epic] Release v2.0 - {key}",
            issue_type=JiraIssueType.EPIC,
            status="In Progress",
            priority="High",
            project_key=project,
            story_points=21.0,
            subtasks=[
                JiraTicket(
                    key=f"{project}-101",
                    summary="Story: User authentication flow",
                    status="Done",
                    issue_type=JiraIssueType.STORY,
                    story_points=8.0,
                    subtasks=[
                        JiraTicket(key=f"{project}-101-1", summary="Implement OAuth", status="Done", issue_type=JiraIssueType.SUBTASK),
                        JiraTicket(key=f"{project}-101-2", summary="Add tests", status="Done", issue_type=JiraIssueType.SUBTASK),
                    ]
                ),
                JiraTicket(
                    key=f"{project}-102",
                    summary="Story: API rate limiting",
                    status="In Progress",
                    issue_type=JiraIssueType.STORY,
                    story_points=5.0
                ),
                JiraTicket(
                    key=f"{project}-103",
                    summary="Story: Dashboard improvements",
                    status="To Do",
                    issue_type=JiraIssueType.STORY,
                    story_points=8.0
                ),
            ]
        )
    
    def _mock_search(self, jql: str, max_results: int) -> JiraSearchResult:
        """Generate mock search results"""
        return JiraSearchResult(
            total=3,
            start_at=0,
            max_results=max_results,
            issues=[
                self._mock_issue("PROJ-101"),
                self._mock_issue("PROJ-102"),
                self._mock_issue("PROJ-103"),
            ]
        )
    
    def _mock_sprint_stats(self, project_key: str, sprint_name: Optional[str]) -> JiraSprintStats:
        """Generate mock sprint stats"""
        return JiraSprintStats(
            sprint_id=42,
            sprint_name=sprint_name or "Sprint 42",
            total_issues=15,
            completed_issues=10,
            in_progress_issues=4,
            blocked_issues=1,
            total_story_points=42.0,
            completed_story_points=28.0,
            completion_percentage=66.7,
            blockers=[f"{project_key}-105"]
        )


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

jira_client: Optional[JiraClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global jira_client
    
    # Startup
    setup_tracing("jira-agent", service_version="2.3.0")
    jira_client = JiraClient()
    
    # Log current mode
    current_mode = await is_mock_mode()
    logger.info(f"Jira Agent started - Mode: {'MOCK' if current_mode else 'LIVE'}")
    
    yield
    
    # Shutdown
    logger.info("Jira Agent shutting down")


app = FastAPI(
    title="Nexus Jira Agent",
    description="Agent for Jira ticket operations with dynamic configuration support",
    version="2.3.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(MetricsMiddleware, agent_type="jira")
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
    """Health check endpoint with dynamic mode detection"""
    current_mode = await is_mock_mode()
    return {
        "status": "healthy",
        "service": "jira-agent",
        "version": "2.3.0",
        "mock_mode": current_mode,
        "dynamic_config": True
    }


@app.get("/issue/{ticket_key}", response_model=AgentTaskResponse)
@track_tool_usage("get_issue", agent_type="jira")
async def get_issue(ticket_key: str):
    """Fetch a single Jira issue by key"""
    task_id = generate_task_id("jira")
    
    try:
        ticket = await jira_client.get_issue(ticket_key)
        JIRA_TICKETS_PROCESSED.labels(action="get", project_key=ticket.project_key or "unknown").inc()
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data=ticket.model_dump(mode="json"),
            agent_type=AgentType.JIRA
        )
    except Exception as e:
        logger.error(f"Failed to fetch issue {ticket_key}: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.JIRA
        )


@app.get("/hierarchy/{ticket_key}", response_model=AgentTaskResponse)
@track_tool_usage("get_ticket_hierarchy", agent_type="jira")
async def get_ticket_hierarchy(
    ticket_key: str,
    max_depth: int = Query(3, ge=1, le=5, description="Maximum depth to traverse")
):
    """Fetch complete ticket hierarchy (Epic -> Stories -> Subtasks)"""
    task_id = generate_task_id("jira")
    
    try:
        hierarchy = await jira_client.get_issue_hierarchy(ticket_key, max_depth=max_depth)
        
        def count_tickets(ticket: JiraTicket) -> int:
            return 1 + sum(count_tickets(st) for st in ticket.subtasks)
        
        total_count = count_tickets(hierarchy)
        
        JIRA_TICKETS_PROCESSED.labels(action="hierarchy", project_key=hierarchy.project_key or "unknown").inc(total_count)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data={
                "hierarchy": hierarchy.model_dump(mode="json"),
                "total_tickets": total_count
            },
            agent_type=AgentType.JIRA
        )
    except Exception as e:
        logger.error(f"Failed to fetch hierarchy for {ticket_key}: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.JIRA
        )


@app.get("/search", response_model=AgentTaskResponse)
@track_tool_usage("search_issues", agent_type="jira")
async def search_issues(
    jql: str = Query(..., description="JQL query string"),
    start_at: int = Query(0, ge=0),
    max_results: int = Query(50, ge=1, le=100)
):
    """Search Jira issues using JQL"""
    task_id = generate_task_id("jira")
    
    try:
        results = await jira_client.search_issues(jql, start_at, max_results)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data=results.model_dump(mode="json"),
            agent_type=AgentType.JIRA
        )
    except Exception as e:
        logger.error(f"Failed to search issues: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.JIRA
        )


@app.post("/update", response_model=AgentTaskResponse)
@track_tool_usage("update_ticket_status", agent_type="jira")
async def update_ticket(
    key: str = Query(..., description="Ticket key"),
    status: Optional[str] = Query(None, description="New status"),
    comment: Optional[str] = Query(None, description="Comment to add")
):
    """Update a Jira ticket's status and/or add a comment"""
    task_id = generate_task_id("jira")
    
    try:
        success = True
        
        if status:
            success = await jira_client.update_issue_status(key, status, comment)
        elif comment:
            success = await jira_client.add_comment(key, comment)
        else:
            return AgentTaskResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_message="Either status or comment must be provided",
                agent_type=AgentType.JIRA
            )
        
        if success:
            JIRA_TICKETS_PROCESSED.labels(action="update", project_key=key.split("-")[0]).inc()
            return AgentTaskResponse(
                task_id=task_id,
                status=TaskStatus.SUCCESS,
                data={"message": f"Updated {key}", "status": status, "comment_added": bool(comment)},
                agent_type=AgentType.JIRA
            )
        else:
            return AgentTaskResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_message=f"Failed to update {key}",
                agent_type=AgentType.JIRA
            )
    except Exception as e:
        logger.error(f"Failed to update ticket {key}: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.JIRA
        )


from pydantic import BaseModel as PydanticBaseModel


class TicketFieldUpdateRequest(PydanticBaseModel):
    """Request body for updating ticket fields"""
    ticket_key: str
    fields: Dict[str, Any]
    updated_by: Optional[str] = None


@app.post("/update-ticket", response_model=AgentTaskResponse)
@track_tool_usage("update_ticket_fields", agent_type="jira")
async def update_ticket_fields(request: TicketFieldUpdateRequest):
    """Update multiple fields on a Jira ticket"""
    task_id = generate_task_id("jira")
    
    try:
        result = await jira_client.update_issue_fields(
            key=request.ticket_key,
            fields=request.fields
        )
        
        if result.get("success"):
            JIRA_TICKETS_PROCESSED.labels(
                action="update_fields",
                project_key=request.ticket_key.split("-")[0]
            ).inc()
            
            return AgentTaskResponse(
                task_id=task_id,
                status=TaskStatus.SUCCESS,
                data={
                    "message": f"Updated {request.ticket_key}",
                    "fields_updated": result.get("fields_updated", []),
                    "updated_by": request.updated_by
                },
                agent_type=AgentType.JIRA
            )
        else:
            return AgentTaskResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_message=result.get("error", f"Failed to update {request.ticket_key}"),
                agent_type=AgentType.JIRA
            )
            
    except Exception as e:
        logger.error(f"Failed to update ticket fields {request.ticket_key}: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.JIRA
        )


@app.get("/sprint-stats/{project_key}", response_model=AgentTaskResponse)
@track_tool_usage("get_sprint_stats", agent_type="jira")
async def get_sprint_stats(
    project_key: str,
    sprint_name: Optional[str] = Query(None, description="Sprint name (optional)")
):
    """Get sprint statistics for release readiness assessment"""
    task_id = generate_task_id("jira")
    
    try:
        stats = await jira_client.get_sprint_stats(project_key, sprint_name)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data=stats.model_dump(mode="json"),
            agent_type=AgentType.JIRA
        )
    except Exception as e:
        logger.error(f"Failed to get sprint stats: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.JIRA
        )


@app.post("/execute", response_model=AgentTaskResponse)
async def execute_task(request: AgentTaskRequest):
    """Generic task execution endpoint for orchestrator integration"""
    action = request.action
    payload = request.payload
    
    if action == "get_issue":
        return await get_issue(payload.get("key"))
    elif action == "get_hierarchy":
        return await get_ticket_hierarchy(payload.get("key"), payload.get("max_depth", 3))
    elif action == "search":
        return await search_issues(
            jql=payload.get("jql"),
            start_at=payload.get("start_at", 0),
            max_results=payload.get("max_results", 50)
        )
    elif action == "update":
        return await update_ticket(
            key=payload.get("key"),
            status=payload.get("status"),
            comment=payload.get("comment")
        )
    elif action == "sprint_stats":
        return await get_sprint_stats(
            project_key=payload.get("project_key"),
            sprint_name=payload.get("sprint_name")
        )
    elif action == "update_fields":
        update_request = TicketFieldUpdateRequest(
            ticket_key=payload.get("ticket_key"),
            fields=payload.get("fields", {}),
            updated_by=payload.get("updated_by")
        )
        return await update_ticket_fields(update_request)
    else:
        return AgentTaskResponse(
            task_id=request.task_id,
            status=TaskStatus.FAILED,
            error_message=f"Unknown action: {action}",
            agent_type=AgentType.JIRA
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
