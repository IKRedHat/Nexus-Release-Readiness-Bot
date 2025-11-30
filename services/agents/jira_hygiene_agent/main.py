"""
Nexus Jira Hygiene Agent
Quality Gatekeeper for Jira Data - Validates ticket completeness and notifies assignees

This agent runs scheduled hygiene checks on Jira tickets to ensure data quality
by validating required fields and calculating compliance scores.
"""
import os
import sys
import logging
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from contextlib import asynccontextmanager
from collections import defaultdict

import pytz
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from prometheus_client import Gauge, Counter

# Add shared lib to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared")))

from nexus_lib.schemas.agent_contract import (
    AgentTaskRequest,
    AgentTaskResponse,
    TaskStatus,
    AgentType,
)
from nexus_lib.middleware import MetricsMiddleware, AuthMiddleware
from nexus_lib.instrumentation import (
    setup_tracing,
    track_tool_usage,
    create_metrics_endpoint,
)
from nexus_lib.utils import AsyncHttpClient, generate_task_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("nexus.jira-hygiene-agent")


# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

HYGIENE_SCORE = Gauge(
    'nexus_project_hygiene_score',
    'Percentage of fully compliant Jira tickets',
    ['project_key']
)

HYGIENE_CHECKS_TOTAL = Counter(
    'nexus_hygiene_checks_total',
    'Total number of hygiene checks performed',
    ['project_key', 'trigger_type']
)

VIOLATIONS_TOTAL = Counter(
    'nexus_hygiene_violations_total',
    'Total number of hygiene violations found',
    ['project_key', 'violation_type']
)

TICKETS_CHECKED = Gauge(
    'nexus_hygiene_tickets_checked',
    'Number of tickets checked in last hygiene run',
    ['project_key']
)

COMPLIANT_TICKETS = Gauge(
    'nexus_hygiene_compliant_tickets',
    'Number of compliant tickets in last hygiene run',
    ['project_key']
)


# ============================================================================
# CONFIGURATION
# ============================================================================

class HygieneConfig(BaseModel):
    """Configuration for hygiene checks"""
    # Required fields to validate
    required_fields: List[str] = Field(
        default=[
            "labels",
            "fixVersions",
            "versions",  # Affected Version
            "customfield_10016",  # Story Points (common field ID)
            "customfield_10001",  # Team/Contributors (common field ID)
        ]
    )
    
    # Human-readable field names for reporting
    field_names: Dict[str, str] = Field(
        default={
            "labels": "Labels",
            "fixVersions": "Fix Version",
            "versions": "Affected Version",
            "customfield_10016": "Story Points",
            "customfield_10001": "Team/Contributors",
        }
    )
    
    # Issue types to check
    issue_types: List[str] = Field(
        default=["Story", "Task", "Bug", "Epic"]
    )
    
    # Statuses to exclude (completed work)
    excluded_statuses: List[str] = Field(
        default=["Done", "Closed", "Cancelled", "Resolved"]
    )
    
    # Projects to check (empty = all)
    projects: List[str] = Field(default=[])
    
    # Timezone for scheduling
    timezone: str = Field(default="UTC")
    
    # Schedule (cron format - weekdays at 9 AM)
    schedule_hour: int = Field(default=9)
    schedule_minute: int = Field(default=0)
    schedule_days: str = Field(default="mon-fri")


# ============================================================================
# DATA MODELS
# ============================================================================

class TicketViolation(BaseModel):
    """A single ticket's hygiene violations"""
    ticket_key: str
    ticket_summary: str
    ticket_url: str
    missing_fields: List[str]
    assignee_email: Optional[str] = None
    assignee_display_name: Optional[str] = None


class AssigneeViolations(BaseModel):
    """Violations grouped by assignee"""
    assignee_email: str
    assignee_display_name: str
    violations: List[TicketViolation]
    total_violations: int


class HygieneCheckResult(BaseModel):
    """Result of a hygiene check run"""
    check_id: str
    timestamp: datetime
    project_key: str
    total_tickets_checked: int
    compliant_tickets: int
    non_compliant_tickets: int
    hygiene_score: float
    violations_by_assignee: List[AssigneeViolations]
    violation_summary: Dict[str, int]  # field_name -> count


class HygieneCheckRequest(BaseModel):
    """Request to run a hygiene check"""
    project_key: Optional[str] = Field(None, description="Specific project to check (optional)")
    notify: bool = Field(True, description="Send notifications to assignees")
    dry_run: bool = Field(False, description="Check without sending notifications")


# ============================================================================
# JIRA CLIENT
# ============================================================================

class JiraHygieneClient:
    """
    Jira client for hygiene checks
    """
    
    def __init__(self, config: HygieneConfig):
        self.config = config
        self.mock_mode = os.environ.get("JIRA_MOCK_MODE", "true").lower() == "true"
        self.jira = None
        self.jira_url = os.environ.get("JIRA_URL", "https://jira.example.com")
        
        if not self.mock_mode:
            try:
                from atlassian import Jira
                self.jira = Jira(
                    url=self.jira_url,
                    username=os.environ.get("JIRA_USERNAME"),
                    password=os.environ.get("JIRA_API_TOKEN"),
                    cloud=os.environ.get("JIRA_CLOUD", "true").lower() == "true"
                )
                logger.info("Jira Hygiene client initialized in LIVE mode")
            except ImportError:
                logger.warning("atlassian-python-api not installed, using mock mode")
                self.mock_mode = True
            except Exception as e:
                logger.error(f"Failed to initialize Jira client: {e}")
                self.mock_mode = True
        
        if self.mock_mode:
            logger.info("Jira Hygiene client running in MOCK mode")
    
    def get_active_sprint_tickets(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch tickets from active sprints/releases"""
        if self.mock_mode:
            return self._get_mock_tickets(project_key)
        
        try:
            # Build JQL for active tickets
            jql_parts = []
            
            # Filter by project if specified
            if project_key:
                jql_parts.append(f"project = {project_key}")
            elif self.config.projects:
                projects_str = ", ".join(self.config.projects)
                jql_parts.append(f"project IN ({projects_str})")
            
            # Filter by issue type
            types_str = ", ".join([f'"{t}"' for t in self.config.issue_types])
            jql_parts.append(f"issuetype IN ({types_str})")
            
            # Exclude completed statuses
            statuses_str = ", ".join([f'"{s}"' for s in self.config.excluded_statuses])
            jql_parts.append(f"status NOT IN ({statuses_str})")
            
            # Active sprint or fix version
            jql_parts.append("(sprint in openSprints() OR fixVersion in unreleasedVersions())")
            
            jql = " AND ".join(jql_parts)
            
            # Fetch tickets
            issues = []
            start_at = 0
            max_results = 100
            
            while True:
                result = self.jira.jql(
                    jql,
                    start=start_at,
                    limit=max_results,
                    fields="*all"
                )
                
                issues.extend(result.get("issues", []))
                
                if len(result.get("issues", [])) < max_results:
                    break
                start_at += max_results
            
            return issues
            
        except Exception as e:
            logger.error(f"Failed to fetch tickets: {e}")
            raise
    
    def _get_mock_tickets(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate mock tickets for testing"""
        project = project_key or "PROJ"
        
        return [
            # Compliant ticket
            {
                "key": f"{project}-101",
                "fields": {
                    "summary": "Implement user authentication",
                    "issuetype": {"name": "Story"},
                    "status": {"name": "In Progress"},
                    "labels": ["backend", "security"],
                    "fixVersions": [{"name": "v2.0.0"}],
                    "versions": [{"name": "v1.9.0"}],
                    "customfield_10016": 8.0,
                    "customfield_10001": {"name": "Platform Team"},
                    "assignee": {
                        "emailAddress": "alice@example.com",
                        "displayName": "Alice Developer"
                    }
                }
            },
            # Missing labels
            {
                "key": f"{project}-102",
                "fields": {
                    "summary": "Fix login timeout issue",
                    "issuetype": {"name": "Bug"},
                    "status": {"name": "In Progress"},
                    "labels": [],  # Missing!
                    "fixVersions": [{"name": "v2.0.0"}],
                    "versions": [{"name": "v1.9.5"}],
                    "customfield_10016": 3.0,
                    "customfield_10001": {"name": "Platform Team"},
                    "assignee": {
                        "emailAddress": "bob@example.com",
                        "displayName": "Bob Engineer"
                    }
                }
            },
            # Missing story points and fix version
            {
                "key": f"{project}-103",
                "fields": {
                    "summary": "Add API rate limiting",
                    "issuetype": {"name": "Task"},
                    "status": {"name": "To Do"},
                    "labels": ["api"],
                    "fixVersions": [],  # Missing!
                    "versions": [],  # Missing!
                    "customfield_10016": None,  # Missing!
                    "customfield_10001": {"name": "API Team"},
                    "assignee": {
                        "emailAddress": "charlie@example.com",
                        "displayName": "Charlie Backend"
                    }
                }
            },
            # Missing team/contributors
            {
                "key": f"{project}-104",
                "fields": {
                    "summary": "Update documentation",
                    "issuetype": {"name": "Task"},
                    "status": {"name": "In Progress"},
                    "labels": ["docs"],
                    "fixVersions": [{"name": "v2.0.0"}],
                    "versions": [{"name": "v1.9.0"}],
                    "customfield_10016": 2.0,
                    "customfield_10001": None,  # Missing!
                    "assignee": {
                        "emailAddress": "alice@example.com",
                        "displayName": "Alice Developer"
                    }
                }
            },
            # Unassigned ticket with multiple violations
            {
                "key": f"{project}-105",
                "fields": {
                    "summary": "Legacy code cleanup",
                    "issuetype": {"name": "Task"},
                    "status": {"name": "To Do"},
                    "labels": [],  # Missing!
                    "fixVersions": [],  # Missing!
                    "versions": [],  # Missing!
                    "customfield_10016": None,  # Missing!
                    "customfield_10001": None,  # Missing!
                    "assignee": None  # Unassigned!
                }
            },
            # Compliant ticket 2
            {
                "key": f"{project}-106",
                "fields": {
                    "summary": "Performance optimization",
                    "issuetype": {"name": "Story"},
                    "status": {"name": "In Review"},
                    "labels": ["performance", "backend"],
                    "fixVersions": [{"name": "v2.0.0"}],
                    "versions": [{"name": "v1.9.0"}],
                    "customfield_10016": 5.0,
                    "customfield_10001": {"name": "Platform Team"},
                    "assignee": {
                        "emailAddress": "bob@example.com",
                        "displayName": "Bob Engineer"
                    }
                }
            },
        ]


# ============================================================================
# HYGIENE CHECKER
# ============================================================================

class HygieneChecker:
    """
    Core hygiene checking logic
    """
    
    def __init__(self, jira_client: JiraHygieneClient, slack_client: AsyncHttpClient, config: HygieneConfig):
        self.jira_client = jira_client
        self.slack_client = slack_client
        self.config = config
    
    def _is_field_empty(self, value: Any) -> bool:
        """Check if a field value is considered empty"""
        if value is None:
            return True
        if isinstance(value, list) and len(value) == 0:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, dict) and not value:
            return True
        return False
    
    def _validate_ticket(self, ticket: Dict[str, Any]) -> List[str]:
        """Validate a ticket and return list of missing field names"""
        missing_fields = []
        fields = ticket.get("fields", {})
        
        for field_id in self.config.required_fields:
            value = fields.get(field_id)
            
            if self._is_field_empty(value):
                # Get human-readable name
                field_name = self.config.field_names.get(field_id, field_id)
                missing_fields.append(field_name)
        
        return missing_fields
    
    def _get_assignee_info(self, ticket: Dict[str, Any]) -> tuple:
        """Extract assignee info from ticket"""
        fields = ticket.get("fields", {})
        assignee = fields.get("assignee")
        
        if assignee:
            return (
                assignee.get("emailAddress", "unknown@example.com"),
                assignee.get("displayName", "Unknown User")
            )
        return ("unassigned@example.com", "Unassigned")
    
    def _build_ticket_url(self, ticket_key: str) -> str:
        """Build Jira ticket URL"""
        base_url = self.jira_client.jira_url.rstrip("/")
        return f"{base_url}/browse/{ticket_key}"
    
    @track_tool_usage("check_hygiene", agent_type="jira_hygiene")
    async def check_hygiene(
        self,
        project_key: Optional[str] = None,
        trigger_type: str = "manual"
    ) -> HygieneCheckResult:
        """
        Run hygiene check on active tickets
        
        Args:
            project_key: Specific project to check (optional)
            trigger_type: "scheduled" or "manual"
        
        Returns:
            HygieneCheckResult with violations and score
        """
        check_id = generate_task_id("hygiene")
        
        # Fetch tickets
        tickets = self.jira_client.get_active_sprint_tickets(project_key)
        project = project_key or "ALL"
        
        logger.info(f"Checking hygiene for {len(tickets)} tickets in {project}")
        
        # Track metrics
        HYGIENE_CHECKS_TOTAL.labels(project_key=project, trigger_type=trigger_type).inc()
        
        # Analyze tickets
        violations_by_assignee: Dict[str, List[TicketViolation]] = defaultdict(list)
        violation_summary: Dict[str, int] = defaultdict(int)
        compliant_count = 0
        
        for ticket in tickets:
            ticket_key = ticket.get("key", "UNKNOWN")
            fields = ticket.get("fields", {})
            
            # Validate ticket
            missing_fields = self._validate_ticket(ticket)
            
            if not missing_fields:
                compliant_count += 1
                continue
            
            # Get assignee
            email, display_name = self._get_assignee_info(ticket)
            
            # Create violation record
            violation = TicketViolation(
                ticket_key=ticket_key,
                ticket_summary=fields.get("summary", "No summary"),
                ticket_url=self._build_ticket_url(ticket_key),
                missing_fields=missing_fields,
                assignee_email=email,
                assignee_display_name=display_name
            )
            
            violations_by_assignee[email].append(violation)
            
            # Update violation counts
            for field in missing_fields:
                violation_summary[field] += 1
                VIOLATIONS_TOTAL.labels(project_key=project, violation_type=field).inc()
        
        # Calculate hygiene score
        total_tickets = len(tickets)
        hygiene_score = (compliant_count / total_tickets * 100) if total_tickets > 0 else 100.0
        
        # Update Prometheus metrics
        HYGIENE_SCORE.labels(project_key=project).set(hygiene_score)
        TICKETS_CHECKED.labels(project_key=project).set(total_tickets)
        COMPLIANT_TICKETS.labels(project_key=project).set(compliant_count)
        
        # Build assignee violation list
        assignee_violations = []
        for email, violations in violations_by_assignee.items():
            if violations:
                assignee_violations.append(AssigneeViolations(
                    assignee_email=email,
                    assignee_display_name=violations[0].assignee_display_name or "Unknown",
                    violations=violations,
                    total_violations=sum(len(v.missing_fields) for v in violations)
                ))
        
        # Sort by violation count (descending)
        assignee_violations.sort(key=lambda x: x.total_violations, reverse=True)
        
        result = HygieneCheckResult(
            check_id=check_id,
            timestamp=datetime.utcnow(),
            project_key=project,
            total_tickets_checked=total_tickets,
            compliant_tickets=compliant_count,
            non_compliant_tickets=total_tickets - compliant_count,
            hygiene_score=hygiene_score,
            violations_by_assignee=assignee_violations,
            violation_summary=dict(violation_summary)
        )
        
        logger.info(
            f"Hygiene check complete: {compliant_count}/{total_tickets} compliant "
            f"({hygiene_score:.1f}% score)"
        )
        
        return result
    
    async def send_notifications(self, result: HygieneCheckResult) -> int:
        """
        Send DM notifications to assignees via Slack Agent
        
        Returns number of notifications sent
        """
        notifications_sent = 0
        slack_agent_url = os.environ.get("SLACK_AGENT_URL", "http://slack-agent:8000")
        
        for assignee in result.violations_by_assignee:
            # Skip unassigned
            if assignee.assignee_email == "unassigned@example.com":
                logger.warning(f"Skipping notification for unassigned tickets")
                continue
            
            # Format the message
            message = self._format_violation_message(assignee, result)
            
            try:
                # Send to Slack Agent's DM endpoint
                response = await self.slack_client.post(
                    f"{slack_agent_url}/send-dm",
                    json_body={
                        "email": assignee.assignee_email,
                        "message": message["text"],
                        "blocks": message.get("blocks")
                    }
                )
                
                if response.get("status") == "success":
                    notifications_sent += 1
                    logger.info(f"Sent hygiene notification to {assignee.assignee_email}")
                else:
                    logger.warning(f"Failed to notify {assignee.assignee_email}: {response}")
                    
            except Exception as e:
                logger.error(f"Error sending notification to {assignee.assignee_email}: {e}")
        
        return notifications_sent
    
    def _format_violation_message(
        self,
        assignee: AssigneeViolations,
        result: HygieneCheckResult
    ) -> Dict[str, Any]:
        """Format violation notification message with interactive buttons"""
        # Build ticket list
        ticket_lines = []
        for v in assignee.violations[:10]:  # Limit to 10 tickets per message
            missing = ", ".join(v.missing_fields)
            ticket_lines.append(f"• <{v.ticket_url}|{v.ticket_key}>: Missing {missing}")
        
        if len(assignee.violations) > 10:
            ticket_lines.append(f"_...and {len(assignee.violations) - 10} more tickets_")
        
        tickets_text = "\n".join(ticket_lines)
        
        # Prepare violation data for modal (limited to first 5 tickets for usability)
        violation_payload = {
            "check_id": result.check_id,
            "assignee_email": assignee.assignee_email,
            "tickets": [
                {
                    "key": v.ticket_key,
                    "summary": v.ticket_summary[:50],  # Truncate for payload size
                    "missing_fields": v.missing_fields
                }
                for v in assignee.violations[:5]
            ]
        }
        
        # Serialize for button value (must be < 2000 chars)
        import json
        violation_value = json.dumps(violation_payload)
        
        # Build Block Kit message with interactive elements
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📋 Jira Ticket Hygiene Report",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hi {assignee.assignee_display_name}! 👋\n\n"
                           f"Our automated hygiene check found *{len(assignee.violations)} tickets* "
                           f"assigned to you that are missing required fields.\n\n"
                           f"*Project Hygiene Score:* {result.hygiene_score:.1f}%"
                }
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Tickets needing attention:*\n{tickets_text}"
                }
            },
            {"type": "divider"},
            {
                "type": "actions",
                "block_id": "hygiene_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔧 Fix Tickets Now",
                            "emoji": True
                        },
                        "style": "primary",
                        "action_id": "open_hygiene_fix_modal",
                        "value": violation_value
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📊 View Full Report",
                            "emoji": True
                        },
                        "action_id": "view_hygiene_report",
                        "url": f"https://nexus.example.com/hygiene/{result.check_id}"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⏰ Remind Me Later",
                            "emoji": True
                        },
                        "action_id": "snooze_hygiene_reminder",
                        "value": json.dumps({
                            "check_id": result.check_id,
                            "assignee_email": assignee.assignee_email
                        })
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🤖 Sent by Nexus Jira Hygiene Agent | "
                               f"Check ID: {result.check_id[:8]}"
                    }
                ]
            }
        ]
        
        text = (
            f"Jira Hygiene Report: {len(assignee.violations)} tickets need attention. "
            f"Project score: {result.hygiene_score:.1f}%"
        )
        
        return {"text": text, "blocks": blocks}


# ============================================================================
# SCHEDULER
# ============================================================================

class HygieneScheduler:
    """APScheduler wrapper for scheduled hygiene checks"""
    
    def __init__(self, checker: HygieneChecker, config: HygieneConfig):
        self.checker = checker
        self.config = config
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(config.timezone))
        self._setup_jobs()
    
    def _setup_jobs(self):
        """Configure scheduled jobs"""
        # Parse days
        day_map = {
            "mon": "0", "tue": "1", "wed": "2", "thu": "3",
            "fri": "4", "sat": "5", "sun": "6"
        }
        
        days = self.config.schedule_days
        if days == "mon-fri":
            day_of_week = "0-4"  # Monday to Friday
        elif days == "daily":
            day_of_week = "*"
        else:
            # Parse custom format like "mon,wed,fri"
            day_list = [day_map.get(d.strip().lower()[:3], d) for d in days.split(",")]
            day_of_week = ",".join(day_list)
        
        # Add the scheduled job
        self.scheduler.add_job(
            self._scheduled_check,
            CronTrigger(
                hour=self.config.schedule_hour,
                minute=self.config.schedule_minute,
                day_of_week=day_of_week,
                timezone=pytz.timezone(self.config.timezone)
            ),
            id="hygiene_check",
            name="Scheduled Hygiene Check",
            replace_existing=True
        )
        
        logger.info(
            f"Scheduled hygiene check: {self.config.schedule_hour:02d}:{self.config.schedule_minute:02d} "
            f"on days {day_of_week} ({self.config.timezone})"
        )
    
    async def _scheduled_check(self):
        """Execute scheduled hygiene check"""
        logger.info("Running scheduled hygiene check")
        
        try:
            # Run check for all configured projects
            result = await self.checker.check_hygiene(
                project_key=None,  # All projects
                trigger_type="scheduled"
            )
            
            # Send notifications
            if result.non_compliant_tickets > 0:
                sent = await self.checker.send_notifications(result)
                logger.info(f"Sent {sent} hygiene notifications")
            else:
                logger.info("No violations found, no notifications sent")
                
        except Exception as e:
            logger.exception(f"Scheduled hygiene check failed: {e}")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Hygiene scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Hygiene scheduler stopped")
    
    def get_next_run(self) -> Optional[datetime]:
        """Get next scheduled run time"""
        job = self.scheduler.get_job("hygiene_check")
        if job:
            return job.next_run_time
        return None


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Global instances
config: Optional[HygieneConfig] = None
jira_client: Optional[JiraHygieneClient] = None
slack_client: Optional[AsyncHttpClient] = None
checker: Optional[HygieneChecker] = None
scheduler: Optional[HygieneScheduler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global config, jira_client, slack_client, checker, scheduler
    
    # Startup
    logger.info("Starting Jira Hygiene Agent...")
    
    setup_tracing("jira-hygiene-agent", service_version="1.0.0")
    
    # Initialize configuration
    config = HygieneConfig(
        projects=os.environ.get("HYGIENE_PROJECTS", "").split(",") if os.environ.get("HYGIENE_PROJECTS") else [],
        timezone=os.environ.get("HYGIENE_TIMEZONE", "UTC"),
        schedule_hour=int(os.environ.get("HYGIENE_SCHEDULE_HOUR", "9")),
        schedule_minute=int(os.environ.get("HYGIENE_SCHEDULE_MINUTE", "0")),
        schedule_days=os.environ.get("HYGIENE_SCHEDULE_DAYS", "mon-fri"),
    )
    
    # Initialize clients
    jira_client = JiraHygieneClient(config)
    slack_client = AsyncHttpClient(timeout=30)
    
    # Initialize checker
    checker = HygieneChecker(jira_client, slack_client, config)
    
    # Initialize and start scheduler
    scheduler = HygieneScheduler(checker, config)
    scheduler.start()
    
    logger.info("Jira Hygiene Agent started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Jira Hygiene Agent...")
    scheduler.stop()
    await slack_client.close()
    logger.info("Jira Hygiene Agent shutdown complete")


app = FastAPI(
    title="Nexus Jira Hygiene Agent",
    description="Quality Gatekeeper for Jira Data - Validates ticket completeness and compliance",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(MetricsMiddleware, agent_type="jira_hygiene")
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
    next_run = scheduler.get_next_run() if scheduler else None
    
    return {
        "status": "healthy",
        "service": "jira-hygiene-agent",
        "mock_mode": jira_client.mock_mode if jira_client else True,
        "scheduler_running": scheduler.scheduler.running if scheduler else False,
        "next_scheduled_run": next_run.isoformat() if next_run else None
    }


@app.post("/run-check", response_model=AgentTaskResponse)
async def run_check(
    request: HygieneCheckRequest,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger a hygiene check
    
    - **project_key**: Specific project to check (optional, checks all if not provided)
    - **notify**: Send DM notifications to assignees (default: true)
    - **dry_run**: Run check without sending notifications (default: false)
    """
    task_id = generate_task_id("hygiene")
    
    try:
        # Run hygiene check
        result = await checker.check_hygiene(
            project_key=request.project_key,
            trigger_type="manual"
        )
        
        # Send notifications in background if not dry run
        notifications_sent = 0
        if request.notify and not request.dry_run and result.non_compliant_tickets > 0:
            notifications_sent = await checker.send_notifications(result)
        
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.SUCCESS,
            data={
                "check_id": result.check_id,
                "project": result.project_key,
                "total_checked": result.total_tickets_checked,
                "compliant": result.compliant_tickets,
                "non_compliant": result.non_compliant_tickets,
                "hygiene_score": result.hygiene_score,
                "violation_summary": result.violation_summary,
                "assignees_notified": notifications_sent,
                "dry_run": request.dry_run
            },
            agent_type=AgentType.JIRA
        )
        
    except Exception as e:
        logger.exception(f"Hygiene check failed: {e}")
        return AgentTaskResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error_message=str(e),
            agent_type=AgentType.JIRA
        )


@app.get("/status")
async def get_status():
    """Get current hygiene status and metrics"""
    next_run = scheduler.get_next_run() if scheduler else None
    
    return {
        "service": "jira-hygiene-agent",
        "config": {
            "projects": config.projects if config else [],
            "required_fields": list(config.field_names.values()) if config else [],
            "schedule": f"{config.schedule_hour:02d}:{config.schedule_minute:02d}" if config else "N/A",
            "schedule_days": config.schedule_days if config else "N/A",
            "timezone": config.timezone if config else "UTC"
        },
        "scheduler": {
            "running": scheduler.scheduler.running if scheduler else False,
            "next_run": next_run.isoformat() if next_run else None
        },
        "jira": {
            "mock_mode": jira_client.mock_mode if jira_client else True,
            "url": jira_client.jira_url if jira_client else None
        }
    }


@app.get("/violations/{project_key}")
async def get_violations(project_key: str):
    """
    Get current violations for a specific project
    
    Runs a check and returns violations without sending notifications
    """
    result = await checker.check_hygiene(
        project_key=project_key,
        trigger_type="api"
    )
    
    return {
        "project": project_key,
        "hygiene_score": result.hygiene_score,
        "total_tickets": result.total_tickets_checked,
        "compliant": result.compliant_tickets,
        "non_compliant": result.non_compliant_tickets,
        "violations_by_assignee": [
            {
                "assignee": av.assignee_display_name,
                "email": av.assignee_email,
                "ticket_count": len(av.violations),
                "tickets": [
                    {
                        "key": v.ticket_key,
                        "summary": v.ticket_summary,
                        "missing_fields": v.missing_fields
                    }
                    for v in av.violations
                ]
            }
            for av in result.violations_by_assignee
        ],
        "violation_summary": result.violation_summary
    }


@app.post("/execute", response_model=AgentTaskResponse)
async def execute_task(request: AgentTaskRequest):
    """
    Generic task execution endpoint for orchestrator integration
    """
    action = request.action
    payload = request.payload
    
    if action == "run_check":
        hygiene_request = HygieneCheckRequest(
            project_key=payload.get("project_key"),
            notify=payload.get("notify", True),
            dry_run=payload.get("dry_run", False)
        )
        return await run_check(hygiene_request, BackgroundTasks())
    else:
        return AgentTaskResponse(
            task_id=request.task_id,
            status=TaskStatus.FAILED,
            error_message=f"Unknown action: {action}",
            agent_type=AgentType.JIRA
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

