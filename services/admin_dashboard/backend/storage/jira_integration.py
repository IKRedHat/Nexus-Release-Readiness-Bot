"""
Enterprise Jira Integration Service

Provides:
- Automatic Jira ticket creation from feature requests
- Intelligent field mapping
- Component-based assignment
- Bidirectional sync
- Retry logic and error handling
- Webhook processing for Jira updates
"""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class JiraConfig:
    """Jira integration configuration"""
    
    # Connection
    base_url: str = field(default_factory=lambda: os.getenv("JIRA_URL", ""))
    username: str = field(default_factory=lambda: os.getenv("JIRA_USERNAME", ""))
    api_token: str = field(default_factory=lambda: os.getenv("JIRA_API_TOKEN", ""))
    
    # Project settings
    project_key: str = field(default_factory=lambda: os.getenv("NEXUS_JIRA_PROJECT", "NEXUS"))
    
    # Issue types mapping
    issue_type_mapping: Dict[str, str] = field(default_factory=lambda: {
        "feature_request": "Story",
        "bug_report": "Bug",
        "improvement": "Improvement",
        "documentation": "Task",
        "question": "Task",
    })
    
    # Priority mapping
    priority_mapping: Dict[str, str] = field(default_factory=lambda: {
        "critical": "Highest",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    })
    
    # Component mapping (component name -> Jira component ID/name)
    component_mapping: Dict[str, str] = field(default_factory=lambda: {
        "orchestrator": "Orchestrator",
        "jira-agent": "Jira Agent",
        "git-ci-agent": "Git/CI Agent",
        "slack-agent": "Slack Agent",
        "reporting-agent": "Reporting Agent",
        "jira-hygiene-agent": "Hygiene Agent",
        "rca-agent": "RCA Agent",
        "analytics": "Analytics",
        "webhooks": "Webhooks",
        "admin-dashboard": "Admin Dashboard",
        "shared-library": "Shared Library",
        "infrastructure": "Infrastructure",
        "documentation": "Documentation",
        "ci-cd": "CI/CD",
    })
    
    # Assignee mapping (component -> default assignee email)
    assignee_mapping: Dict[str, str] = field(default_factory=lambda: {
        "orchestrator": os.getenv("NEXUS_ORCHESTRATOR_LEAD", ""),
        "jira-agent": os.getenv("NEXUS_JIRA_AGENT_LEAD", ""),
        "git-ci-agent": os.getenv("NEXUS_GIT_AGENT_LEAD", ""),
        "slack-agent": os.getenv("NEXUS_SLACK_AGENT_LEAD", ""),
        "admin-dashboard": os.getenv("NEXUS_ADMIN_LEAD", ""),
        "infrastructure": os.getenv("NEXUS_INFRA_LEAD", ""),
        "documentation": os.getenv("NEXUS_DOCS_LEAD", ""),
    })
    
    # Default assignee if component not mapped
    default_assignee: str = field(default_factory=lambda: os.getenv("NEXUS_DEFAULT_ASSIGNEE", ""))
    
    # Labels
    label_prefix: str = "nexus-"
    auto_labels: List[str] = field(default_factory=lambda: ["nexus", "feature-request-form"])
    
    # Workflow
    auto_transition_to: Optional[str] = None  # e.g., "In Review"
    
    # Custom fields (customize based on your Jira setup)
    custom_fields: Dict[str, str] = field(default_factory=lambda: {
        "business_value": os.getenv("JIRA_CUSTOM_FIELD_BUSINESS_VALUE", ""),
        "acceptance_criteria": os.getenv("JIRA_CUSTOM_FIELD_AC", ""),
        "environment": "environment",  # Standard field
        "source": os.getenv("JIRA_CUSTOM_FIELD_SOURCE", ""),
    })
    
    # Feature flags
    enabled: bool = field(default_factory=lambda: os.getenv("NEXUS_JIRA_ENABLED", "true").lower() == "true")
    dry_run: bool = field(default_factory=lambda: os.getenv("NEXUS_JIRA_DRY_RUN", "false").lower() == "true")
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    
    @property
    def is_configured(self) -> bool:
        """Check if Jira is properly configured."""
        return bool(self.base_url and self.username and self.api_token)


class JiraError(Exception):
    """Jira integration error"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class TicketCreationResult(Enum):
    """Result of ticket creation attempt"""
    SUCCESS = "success"
    SKIPPED = "skipped"  # Jira disabled or dry run
    FAILED = "failed"
    RETRY_NEEDED = "retry_needed"


# =============================================================================
# Jira Client
# =============================================================================

class JiraClient:
    """Low-level Jira API client with retry logic."""
    
    def __init__(self, config: JiraConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                auth=(self.config.username, self.config.api_token),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=30.0,
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Make a request to Jira API with retry logic."""
        client = await self._get_client()
        
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    json=data,
                    params=params,
                )
                
                if response.status_code >= 400:
                    error_body = response.json() if response.content else {}
                    
                    # Don't retry client errors (4xx)
                    if response.status_code < 500:
                        raise JiraError(
                            f"Jira API error: {response.status_code}",
                            status_code=response.status_code,
                            response=error_body,
                        )
                    
                    # Retry server errors (5xx)
                    last_error = JiraError(
                        f"Jira server error: {response.status_code}",
                        status_code=response.status_code,
                        response=error_body,
                    )
                else:
                    return response.json() if response.content else {}
                
            except httpx.TimeoutException as e:
                last_error = JiraError(f"Request timeout: {e}")
            except httpx.ConnectError as e:
                last_error = JiraError(f"Connection error: {e}")
            
            # Wait before retry
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        raise last_error or JiraError("Unknown error")
    
    async def create_issue(self, fields: Dict) -> Dict:
        """Create a Jira issue."""
        return await self.request("POST", "/rest/api/3/issue", data={"fields": fields})
    
    async def update_issue(self, issue_key: str, fields: Dict) -> Dict:
        """Update a Jira issue."""
        return await self.request("PUT", f"/rest/api/3/issue/{issue_key}", data={"fields": fields})
    
    async def get_issue(self, issue_key: str) -> Dict:
        """Get a Jira issue."""
        return await self.request("GET", f"/rest/api/3/issue/{issue_key}")
    
    async def add_comment(self, issue_key: str, comment: str) -> Dict:
        """Add a comment to an issue."""
        body = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment}]
                    }
                ]
            }
        }
        return await self.request("POST", f"/rest/api/3/issue/{issue_key}/comment", data=body)
    
    async def transition_issue(self, issue_key: str, transition_name: str) -> bool:
        """Transition an issue to a new status."""
        # Get available transitions
        transitions = await self.request("GET", f"/rest/api/3/issue/{issue_key}/transitions")
        
        for transition in transitions.get("transitions", []):
            if transition["name"].lower() == transition_name.lower():
                await self.request(
                    "POST",
                    f"/rest/api/3/issue/{issue_key}/transitions",
                    data={"transition": {"id": transition["id"]}}
                )
                return True
        
        return False
    
    async def search_user(self, email: str) -> Optional[str]:
        """Search for a user by email and return account ID."""
        try:
            result = await self.request(
                "GET",
                "/rest/api/3/user/search",
                params={"query": email}
            )
            
            if result and len(result) > 0:
                return result[0].get("accountId")
        except JiraError:
            pass
        
        return None
    
    async def get_project_components(self) -> List[Dict]:
        """Get components for the project."""
        return await self.request("GET", f"/rest/api/3/project/{self.config.project_key}/components")


# =============================================================================
# Jira Ticket Service
# =============================================================================

class JiraTicketService:
    """
    Enterprise service for creating and managing Jira tickets from feature requests.
    
    Features:
    - Intelligent field mapping
    - Component-based assignment
    - Retry with exponential backoff
    - Bidirectional sync support
    - Webhook processing
    """
    
    def __init__(self, config: Optional[JiraConfig] = None):
        self.config = config or JiraConfig()
        self.client = JiraClient(self.config) if self.config.is_configured else None
        self._component_cache: Optional[Dict[str, str]] = None
        self._user_cache: Dict[str, str] = {}
    
    async def close(self):
        """Clean up resources."""
        if self.client:
            await self.client.close()
    
    # =========================================================================
    # Ticket Creation
    # =========================================================================
    
    async def create_ticket(
        self, 
        feature_request: Dict[str, Any],
        on_success: Optional[callable] = None,
    ) -> Tuple[TicketCreationResult, Optional[Dict]]:
        """
        Create a Jira ticket from a feature request.
        
        Args:
            feature_request: Feature request data
            on_success: Callback function on successful creation
            
        Returns:
            Tuple of (result_status, ticket_data)
        """
        # Check if Jira is enabled
        if not self.config.enabled:
            logger.info("Jira integration disabled, skipping ticket creation")
            return TicketCreationResult.SKIPPED, None
        
        if not self.config.is_configured:
            logger.warning("Jira not configured, skipping ticket creation")
            return TicketCreationResult.SKIPPED, None
        
        # Build ticket fields
        fields = await self._build_ticket_fields(feature_request)
        
        # Dry run mode
        if self.config.dry_run:
            logger.info(f"DRY RUN: Would create Jira ticket with fields: {json.dumps(fields, indent=2)}")
            return TicketCreationResult.SKIPPED, {"dry_run": True, "fields": fields}
        
        try:
            # Create the ticket
            result = await self.client.create_issue(fields)
            
            ticket_key = result.get("key")
            ticket_url = f"{self.config.base_url}/browse/{ticket_key}"
            
            logger.info(f"Created Jira ticket {ticket_key} for feature request {feature_request.get('id')}")
            
            # Auto-transition if configured
            if self.config.auto_transition_to:
                try:
                    await self.client.transition_issue(ticket_key, self.config.auto_transition_to)
                except Exception as e:
                    logger.warning(f"Failed to auto-transition ticket: {e}")
            
            # Add creation comment
            await self._add_creation_comment(ticket_key, feature_request)
            
            # Callback
            if on_success:
                await on_success({
                    "jira_key": ticket_key,
                    "jira_url": ticket_url,
                    "jira_id": result.get("id"),
                })
            
            return TicketCreationResult.SUCCESS, {
                "key": ticket_key,
                "url": ticket_url,
                "id": result.get("id"),
                "self": result.get("self"),
            }
            
        except JiraError as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            
            if e.status_code and e.status_code >= 500:
                return TicketCreationResult.RETRY_NEEDED, {"error": str(e)}
            
            return TicketCreationResult.FAILED, {"error": str(e), "response": e.response}
        
        except Exception as e:
            logger.error(f"Unexpected error creating Jira ticket: {e}")
            return TicketCreationResult.FAILED, {"error": str(e)}
    
    async def _build_ticket_fields(self, feature_request: Dict) -> Dict:
        """Build Jira ticket fields from feature request."""
        req_type = feature_request.get("type", "feature_request")
        priority = feature_request.get("priority", "medium")
        component = feature_request.get("component")
        
        # Base fields
        fields = {
            "project": {"key": self.config.project_key},
            "summary": self._sanitize_summary(feature_request.get("title", "Untitled")),
            "description": await self._build_description(feature_request),
            "issuetype": {"name": self.config.issue_type_mapping.get(req_type, "Task")},
            "priority": {"name": self.config.priority_mapping.get(priority, "Medium")},
        }
        
        # Labels
        labels = list(self.config.auto_labels)
        labels.append(f"{self.config.label_prefix}{req_type}")
        
        if feature_request.get("labels"):
            labels.extend([f"{self.config.label_prefix}{l}" for l in feature_request["labels"]])
        
        fields["labels"] = labels
        
        # Component
        if component:
            jira_component = self.config.component_mapping.get(component, component)
            fields["components"] = [{"name": jira_component}]
        
        # Assignee
        assignee_email = self._get_assignee_email(component)
        if assignee_email:
            assignee_id = await self._resolve_user(assignee_email)
            if assignee_id:
                fields["assignee"] = {"accountId": assignee_id}
        
        # Environment (for bugs)
        if req_type == "bug_report" and feature_request.get("environment"):
            fields["environment"] = feature_request["environment"]
        
        # Custom fields
        await self._add_custom_fields(fields, feature_request)
        
        return fields
    
    async def _build_description(self, feature_request: Dict) -> Dict:
        """Build Jira Atlassian Document Format (ADF) description."""
        req_type = feature_request.get("type", "feature_request")
        
        content = []
        
        # Submitter info
        content.append(self._adf_panel(
            "info",
            f"Submitted by: {feature_request.get('submitter_name', 'Unknown')} "
            f"({feature_request.get('submitter_email', '')})\n"
            f"Source: Nexus Admin Dashboard\n"
            f"Request ID: {feature_request.get('id', 'N/A')}"
        ))
        
        # Main description
        content.append(self._adf_heading("Description", 2))
        content.append(self._adf_paragraph(feature_request.get("description", "")))
        
        # Type-specific sections
        if req_type == "bug_report":
            if feature_request.get("steps_to_reproduce"):
                content.append(self._adf_heading("Steps to Reproduce", 2))
                content.append(self._adf_paragraph(feature_request["steps_to_reproduce"]))
            
            if feature_request.get("expected_behavior"):
                content.append(self._adf_heading("Expected Behavior", 2))
                content.append(self._adf_paragraph(feature_request["expected_behavior"]))
            
            if feature_request.get("actual_behavior"):
                content.append(self._adf_heading("Actual Behavior", 2))
                content.append(self._adf_paragraph(feature_request["actual_behavior"]))
            
            if feature_request.get("browser"):
                content.append(self._adf_heading("Browser", 3))
                content.append(self._adf_paragraph(feature_request["browser"]))
        
        else:  # Feature request / improvement
            if feature_request.get("use_case"):
                content.append(self._adf_heading("Use Case", 2))
                content.append(self._adf_paragraph(feature_request["use_case"]))
            
            if feature_request.get("business_value"):
                content.append(self._adf_heading("Business Value", 2))
                content.append(self._adf_paragraph(feature_request["business_value"]))
            
            if feature_request.get("acceptance_criteria"):
                content.append(self._adf_heading("Acceptance Criteria", 2))
                content.append(self._adf_paragraph(feature_request["acceptance_criteria"]))
        
        return {
            "type": "doc",
            "version": 1,
            "content": content,
        }
    
    def _adf_paragraph(self, text: str) -> Dict:
        """Create ADF paragraph node."""
        return {
            "type": "paragraph",
            "content": [{"type": "text", "text": text or "(not provided)"}]
        }
    
    def _adf_heading(self, text: str, level: int = 2) -> Dict:
        """Create ADF heading node."""
        return {
            "type": "heading",
            "attrs": {"level": level},
            "content": [{"type": "text", "text": text}]
        }
    
    def _adf_panel(self, panel_type: str, text: str) -> Dict:
        """Create ADF panel node."""
        return {
            "type": "panel",
            "attrs": {"panelType": panel_type},
            "content": [self._adf_paragraph(text)]
        }
    
    async def _add_custom_fields(self, fields: Dict, feature_request: Dict):
        """Add custom field values if configured."""
        # Business value
        if (self.config.custom_fields.get("business_value") and 
            feature_request.get("business_value")):
            fields[self.config.custom_fields["business_value"]] = feature_request["business_value"]
        
        # Acceptance criteria
        if (self.config.custom_fields.get("acceptance_criteria") and 
            feature_request.get("acceptance_criteria")):
            fields[self.config.custom_fields["acceptance_criteria"]] = feature_request["acceptance_criteria"]
        
        # Source tracking
        if self.config.custom_fields.get("source"):
            fields[self.config.custom_fields["source"]] = "Nexus Admin Dashboard"
    
    async def _add_creation_comment(self, ticket_key: str, feature_request: Dict):
        """Add a comment noting the automated creation."""
        try:
            comment = (
                f"This ticket was automatically created from the Nexus Admin Dashboard.\n\n"
                f"• Request Type: {feature_request.get('type', 'Unknown')}\n"
                f"• Priority: {feature_request.get('priority', 'Unknown')}\n"
                f"• Component: {feature_request.get('component', 'Not specified')}\n"
                f"• Submitter: {feature_request.get('submitter_name', 'Unknown')}\n"
                f"• Internal ID: {feature_request.get('id', 'N/A')}"
            )
            await self.client.add_comment(ticket_key, comment)
        except Exception as e:
            logger.warning(f"Failed to add creation comment: {e}")
    
    def _sanitize_summary(self, summary: str) -> str:
        """Sanitize summary for Jira (max 255 chars, no newlines)."""
        summary = summary.replace("\n", " ").replace("\r", " ")
        summary = re.sub(r"\s+", " ", summary).strip()
        if len(summary) > 250:
            summary = summary[:247] + "..."
        return summary
    
    def _get_assignee_email(self, component: Optional[str]) -> Optional[str]:
        """Get assignee email for component."""
        if component and component in self.config.assignee_mapping:
            email = self.config.assignee_mapping[component]
            if email:
                return email
        
        return self.config.default_assignee or None
    
    async def _resolve_user(self, email: str) -> Optional[str]:
        """Resolve email to Jira account ID with caching."""
        if email in self._user_cache:
            return self._user_cache[email]
        
        if self.client:
            account_id = await self.client.search_user(email)
            if account_id:
                self._user_cache[email] = account_id
            return account_id
        
        return None
    
    # =========================================================================
    # Sync Operations
    # =========================================================================
    
    async def sync_status(self, feature_request: Dict) -> Optional[str]:
        """
        Sync status from Jira back to feature request.
        
        Returns the Jira status if found, None otherwise.
        """
        jira_key = feature_request.get("jira_key")
        if not jira_key or not self.client:
            return None
        
        try:
            issue = await self.client.get_issue(jira_key)
            return issue.get("fields", {}).get("status", {}).get("name")
        except JiraError:
            return None
    
    async def update_ticket(
        self, 
        jira_key: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update a Jira ticket."""
        if not self.client:
            return False
        
        try:
            # Map updates to Jira fields
            fields = {}
            
            if "priority" in updates:
                fields["priority"] = {
                    "name": self.config.priority_mapping.get(updates["priority"], "Medium")
                }
            
            if "status" in updates and updates["status"] == "completed":
                # Add resolution
                fields["resolution"] = {"name": "Done"}
            
            if fields:
                await self.client.update_issue(jira_key, fields)
            
            return True
            
        except JiraError as e:
            logger.error(f"Failed to update Jira ticket {jira_key}: {e}")
            return False
    
    # =========================================================================
    # Webhook Processing
    # =========================================================================
    
    async def process_webhook(self, payload: Dict) -> Dict[str, Any]:
        """
        Process incoming Jira webhook for bidirectional sync.
        
        Returns dict with action taken and any updates needed.
        """
        webhook_event = payload.get("webhookEvent")
        issue = payload.get("issue", {})
        issue_key = issue.get("key")
        
        if not issue_key:
            return {"action": "ignored", "reason": "no_issue_key"}
        
        # Check if this is a Nexus-created ticket
        labels = issue.get("fields", {}).get("labels", [])
        if "nexus" not in labels and "nexus-" not in str(labels):
            return {"action": "ignored", "reason": "not_nexus_ticket"}
        
        result = {
            "action": "processed",
            "jira_key": issue_key,
            "event": webhook_event,
            "updates": {},
        }
        
        # Handle different webhook events
        if webhook_event == "jira:issue_updated":
            changelog = payload.get("changelog", {}).get("items", [])
            
            for change in changelog:
                field = change.get("field")
                
                if field == "status":
                    new_status = change.get("toString")
                    result["updates"]["jira_status"] = new_status
                    
                    # Map Jira status to feature request status
                    status_mapping = {
                        "Done": "completed",
                        "Closed": "completed",
                        "In Progress": "in_progress",
                        "In Review": "in_progress",
                        "To Do": "triaged",
                        "Open": "triaged",
                        "Won't Do": "rejected",
                        "Rejected": "rejected",
                    }
                    
                    if new_status in status_mapping:
                        result["updates"]["status"] = status_mapping[new_status]
                
                elif field == "resolution":
                    resolution = change.get("toString")
                    if resolution in ["Won't Fix", "Duplicate", "Invalid"]:
                        result["updates"]["status"] = "rejected"
        
        elif webhook_event == "jira:issue_deleted":
            result["updates"]["status"] = "deleted"
            result["updates"]["jira_key"] = None
        
        return result


# =============================================================================
# Background Job Queue
# =============================================================================

class JiraJobQueue:
    """
    Background job queue for Jira operations.
    
    Provides:
    - Async processing
    - Retry with exponential backoff
    - Dead letter queue for failed jobs
    """
    
    def __init__(self, jira_service: JiraTicketService, repository=None):
        self.jira_service = jira_service
        self.repository = repository
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._failed_jobs: List[Dict] = []
    
    async def start(self):
        """Start the background worker."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Jira job queue worker started")
    
    async def stop(self):
        """Stop the background worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Jira job queue worker stopped")
    
    async def enqueue(self, feature_request: Dict):
        """Add a feature request to the queue for Jira ticket creation."""
        await self._queue.put({
            "type": "create_ticket",
            "feature_request": feature_request,
            "attempts": 0,
            "enqueued_at": datetime.utcnow().isoformat(),
        })
        logger.debug(f"Enqueued Jira job for request {feature_request.get('id')}")
    
    async def _worker(self):
        """Background worker that processes jobs."""
        while self._running:
            try:
                # Get job with timeout
                try:
                    job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Process job
                await self._process_job(job)
                self._queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    async def _process_job(self, job: Dict):
        """Process a single job."""
        job_type = job.get("type")
        
        if job_type == "create_ticket":
            feature_request = job["feature_request"]
            
            async def on_success(jira_data: Dict):
                """Update feature request with Jira data."""
                if self.repository:
                    await self.repository.update(
                        feature_request["id"],
                        {
                            "jira_key": jira_data["jira_key"],
                            "jira_url": jira_data["jira_url"],
                            "status": "triaged",
                        },
                        "system"
                    )
            
            result, data = await self.jira_service.create_ticket(
                feature_request,
                on_success=on_success
            )
            
            if result == TicketCreationResult.RETRY_NEEDED:
                job["attempts"] += 1
                
                if job["attempts"] < 3:
                    # Re-queue with backoff
                    await asyncio.sleep(2 ** job["attempts"])
                    await self._queue.put(job)
                else:
                    # Move to failed jobs
                    self._failed_jobs.append(job)
                    logger.error(f"Job failed after {job['attempts']} attempts: {feature_request.get('id')}")
            
            elif result == TicketCreationResult.FAILED:
                self._failed_jobs.append(job)
                logger.error(f"Job permanently failed: {feature_request.get('id')}")
    
    def get_queue_stats(self) -> Dict:
        """Get queue statistics."""
        return {
            "pending": self._queue.qsize(),
            "failed": len(self._failed_jobs),
            "running": self._running,
        }
    
    def get_failed_jobs(self) -> List[Dict]:
        """Get list of failed jobs."""
        return self._failed_jobs.copy()
    
    async def retry_failed(self) -> int:
        """Retry all failed jobs."""
        count = len(self._failed_jobs)
        for job in self._failed_jobs:
            job["attempts"] = 0
            await self._queue.put(job)
        self._failed_jobs.clear()
        return count


# Singleton instances
_jira_service: Optional[JiraTicketService] = None
_job_queue: Optional[JiraJobQueue] = None


async def get_jira_service() -> JiraTicketService:
    """Get or create Jira service singleton."""
    global _jira_service
    if _jira_service is None:
        _jira_service = JiraTicketService()
    return _jira_service


async def get_job_queue() -> JiraJobQueue:
    """Get or create job queue singleton."""
    global _job_queue
    if _job_queue is None:
        from .feature_request_repository import get_repository
        jira_service = await get_jira_service()
        repository = await get_repository()
        _job_queue = JiraJobQueue(jira_service, repository)
        await _job_queue.start()
    return _job_queue

