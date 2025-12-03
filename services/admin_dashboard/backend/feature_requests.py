"""
Enterprise Feature Request and Bug Report Service

Provides comprehensive management of feature requests with:
- Persistent Redis-backed storage
- Automatic Jira ticket creation with component assignment
- Background job processing
- Audit trail
- Notifications
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from nexus_lib.schemas.rbac import (
    FeatureRequest, FeatureRequestCreate, FeatureRequestUpdate,
    RequestType, Priority, RequestStatus,
    JiraFieldMapping,
)

# Import enterprise storage layer
from storage import (
    FeatureRequestRepository,
    JiraTicketService,
    JiraConfig,
    NotificationService,
)
from storage.feature_request_repository import get_repository
from storage.jira_integration import get_jira_service, get_job_queue, TicketCreationResult
from storage.notification_service import get_notification_service

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class FeatureRequestConfig:
    """Feature request service configuration"""
    
    # Jira settings (loaded from environment)
    JIRA_PROJECT_KEY = os.getenv("NEXUS_JIRA_PROJECT", "NEXUS")
    JIRA_AGENT_URL = os.getenv("JIRA_AGENT_URL", "http://localhost:8081")
    
    # Auto-create Jira tickets
    AUTO_CREATE_JIRA = os.getenv("NEXUS_AUTO_CREATE_JIRA", "true").lower() == "true"
    
    # Use background queue for Jira creation
    USE_BACKGROUND_QUEUE = os.getenv("NEXUS_JIRA_ASYNC", "true").lower() == "true"
    
    # Notifications
    NOTIFY_ON_CREATE = os.getenv("NEXUS_NOTIFY_ON_CREATE", "true").lower() == "true"
    NOTIFY_ON_STATUS_CHANGE = os.getenv("NEXUS_NOTIFY_ON_STATUS", "true").lower() == "true"


# =============================================================================
# ENTERPRISE FEATURE REQUEST SERVICE
# =============================================================================

class FeatureRequestService:
    """
    Enterprise service for managing feature requests and bug reports.
    
    Features:
    - Persistent storage with Redis
    - Automatic Jira ticket creation
    - Component-based assignment
    - Background job processing
    - Comprehensive audit trail
    - Slack/webhook notifications
    """
    
    _instance: Optional['FeatureRequestService'] = None
    
    def __init__(self):
        self.repository: Optional[FeatureRequestRepository] = None
        self.jira_service: Optional[JiraTicketService] = None
        self.notification_service: Optional[NotificationService] = None
        self._initialized = False
    
    @classmethod
    async def get_instance(cls) -> 'FeatureRequestService':
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self):
        """Initialize all services."""
        if self._initialized:
            return
        
        self.repository = await get_repository()
        self.jira_service = await get_jira_service()
        self.notification_service = await get_notification_service()
        
        # Start background job queue if enabled
        if FeatureRequestConfig.USE_BACKGROUND_QUEUE:
            await get_job_queue()
        
        self._initialized = True
        logger.info("FeatureRequestService initialized")
    
    # =========================================================================
    # CRUD Operations
    # =========================================================================
    
    async def create_request(
        self,
        data: FeatureRequestCreate,
        submitter_id: str,
        submitter_email: str,
        submitter_name: str,
    ) -> FeatureRequest:
        """
        Create a new feature request or bug report.
        
        This will:
        1. Store the request in persistent storage
        2. Create a Jira ticket (if configured)
        3. Send notifications
        4. Return the created request
        """
        # Prepare request data
        request_data = {
            "type": data.type,
            "title": data.title,
            "description": data.description,
            "priority": data.priority,
            "component": data.component,
            "labels": data.labels,
            "steps_to_reproduce": data.steps_to_reproduce,
            "expected_behavior": data.expected_behavior,
            "actual_behavior": data.actual_behavior,
            "environment": data.environment,
            "browser": data.browser,
            "use_case": data.use_case,
            "business_value": data.business_value,
            "acceptance_criteria": data.acceptance_criteria,
            "submitter_id": submitter_id,
            "submitter_email": submitter_email,
            "submitter_name": submitter_name,
            "status": RequestStatus.SUBMITTED,
        }
        
        # Store in repository
        record = await self.repository.create(request_data, submitter_id)
        
        # Create Jira ticket
        jira_data = None
        if FeatureRequestConfig.AUTO_CREATE_JIRA:
            jira_data = await self._create_jira_ticket(record)
            
            # Update record with Jira data
            if jira_data:
                record = await self.repository.update(
                    record["id"],
                    {
                        "jira_key": jira_data.get("key"),
                        "jira_url": jira_data.get("url"),
                        "status": RequestStatus.TRIAGED,
                    },
                    "system"
                )
        
        # Send notifications
        if FeatureRequestConfig.NOTIFY_ON_CREATE:
            await self._send_notifications(record, jira_data)
        
        logger.info(f"Created feature request {record['id']} by {submitter_email}")
        
        return self._to_model(record)
    
    async def get_request(self, request_id: str) -> Optional[FeatureRequest]:
        """Get a feature request by ID."""
        record = await self.repository.get(request_id)
        if record:
            return self._to_model(record)
        return None
    
    async def update_request(
        self, 
        request_id: str, 
        data: FeatureRequestUpdate,
        updated_by: str = "system",
    ) -> Optional[FeatureRequest]:
        """
        Update a feature request.
        
        Handles:
        - Status change notifications
        - Jira ticket sync (if linked)
        """
        old_record = await self.repository.get(request_id)
        if not old_record:
            return None
        
        old_status = old_record.get("status")
        
        # Apply updates
        updates = data.model_dump(exclude_unset=True)
        record = await self.repository.update(request_id, updates, updated_by)
        
        if not record:
            return None
        
        # Status change handling
        new_status = record.get("status")
        if old_status != new_status:
            # Notify on status change
            if FeatureRequestConfig.NOTIFY_ON_STATUS_CHANGE:
                await self.notification_service.notify_status_change(
                    record, old_status, new_status, updated_by
                )
            
            # Sync to Jira
            if record.get("jira_key"):
                await self.jira_service.update_ticket(
                    record["jira_key"],
                    {"status": new_status}
                )
        
        return self._to_model(record)
    
    async def delete_request(self, request_id: str, deleted_by: str) -> bool:
        """Delete a feature request (soft delete)."""
        return await self.repository.delete(request_id, deleted_by)
    
    # =========================================================================
    # Query Operations
    # =========================================================================
    
    async def list_requests(
        self,
        type_filter: Optional[RequestType] = None,
        status_filter: Optional[RequestStatus] = None,
        priority_filter: Optional[Priority] = None,
        component_filter: Optional[str] = None,
        submitter_id: Optional[str] = None,
        search_term: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[FeatureRequest]:
        """List feature requests with optional filters."""
        results, _ = await self.repository.list(
            type_filter=type_filter.value if type_filter else None,
            status_filter=status_filter.value if status_filter else None,
            priority_filter=priority_filter.value if priority_filter else None,
            component_filter=component_filter,
            submitter_id=submitter_id,
            search_term=search_term,
            limit=limit,
            offset=offset,
        )
        
        return [self._to_model(r) for r in results]
    
    async def get_stats(self) -> Dict:
        """Get aggregated statistics."""
        return await self.repository.get_stats()
    
    async def get_audit_trail(self, request_id: str, limit: int = 50) -> List[Dict]:
        """Get audit trail for a request."""
        return await self.repository.get_audit_trail(request_id, limit)
    
    # =========================================================================
    # Jira Integration
    # =========================================================================
    
    async def _create_jira_ticket(self, record: Dict) -> Optional[Dict]:
        """Create Jira ticket for a feature request."""
        if FeatureRequestConfig.USE_BACKGROUND_QUEUE:
            # Use background queue
            job_queue = await get_job_queue()
            await job_queue.enqueue(record)
            return None  # Jira data will be updated async
        else:
            # Synchronous creation
            result, data = await self.jira_service.create_ticket(record)
            
            if result == TicketCreationResult.SUCCESS:
                return data
            
            return None
    
    async def sync_with_jira(self, request_id: str) -> Optional[str]:
        """
        Sync status from Jira back to feature request.
        
        Returns the updated status if changed, None otherwise.
        """
        record = await self.repository.get(request_id)
        if not record or not record.get("jira_key"):
            return None
        
        jira_status = await self.jira_service.sync_status(record)
        
        if jira_status:
            # Map Jira status to our status
            status_mapping = {
                "Done": RequestStatus.COMPLETED,
                "Closed": RequestStatus.COMPLETED,
                "In Progress": RequestStatus.IN_PROGRESS,
                "In Review": RequestStatus.IN_PROGRESS,
                "To Do": RequestStatus.TRIAGED,
                "Open": RequestStatus.TRIAGED,
                "Won't Do": RequestStatus.REJECTED,
                "Rejected": RequestStatus.REJECTED,
            }
            
            new_status = status_mapping.get(jira_status)
            
            if new_status and new_status != record.get("status"):
                await self.repository.update(
                    request_id,
                    {"status": new_status, "jira_status": jira_status},
                    "jira_sync"
                )
                return new_status
        
        return None
    
    async def process_jira_webhook(self, payload: Dict) -> Dict:
        """Process incoming Jira webhook."""
        result = await self.jira_service.process_webhook(payload)
        
        # If we have updates, apply them
        if result.get("action") == "processed" and result.get("updates"):
            jira_key = result.get("jira_key")
            
            # Find feature request by Jira key
            record = await self.repository.get_by_jira_key(jira_key)
            
            if record:
                await self.repository.update(
                    record["id"],
                    result["updates"],
                    "jira_webhook"
                )
        
        return result
    
    # =========================================================================
    # Notifications
    # =========================================================================
    
    async def _send_notifications(self, record: Dict, jira_data: Optional[Dict]):
        """Send notifications for new request."""
        try:
            await self.notification_service.notify_new_request(record, jira_data)
        except Exception as e:
            logger.error(f"Failed to send notifications: {e}")
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    @staticmethod
    def get_available_components() -> List[str]:
        """Get list of available components."""
        return [
            "orchestrator",
            "jira-agent",
            "git-ci-agent",
            "slack-agent",
            "reporting-agent",
            "jira-hygiene-agent",
            "rca-agent",
            "analytics",
            "webhooks",
            "admin-dashboard",
            "shared-library",
            "infrastructure",
            "documentation",
            "ci-cd",
            "other",
        ]
    
    @staticmethod
    def get_available_labels() -> List[str]:
        """Get list of available labels."""
        return [
            "ui",
            "api",
            "performance",
            "security",
            "accessibility",
            "mobile",
            "integration",
            "data",
            "reporting",
            "notification",
            "authentication",
            "configuration",
            "monitoring",
            "deployment",
            "testing",
        ]
    
    # =========================================================================
    # Field Mapping Configuration
    # =========================================================================
    
    async def get_jira_config(self) -> JiraConfig:
        """Get current Jira configuration."""
        return self.jira_service.config if self.jira_service else JiraConfig()
    
    async def update_jira_config(self, config: Dict) -> JiraConfig:
        """Update Jira configuration (runtime only)."""
        if self.jira_service:
            for key, value in config.items():
                if hasattr(self.jira_service.config, key):
                    setattr(self.jira_service.config, key, value)
        return self.jira_service.config if self.jira_service else JiraConfig()
    
    # =========================================================================
    # Background Job Management
    # =========================================================================
    
    async def get_job_queue_stats(self) -> Dict:
        """Get background job queue statistics."""
        job_queue = await get_job_queue()
        return job_queue.get_queue_stats()
    
    async def retry_failed_jobs(self) -> int:
        """Retry failed Jira creation jobs."""
        job_queue = await get_job_queue()
        return await job_queue.retry_failed()
    
    # =========================================================================
    # Export
    # =========================================================================
    
    async def export_requests(
        self, 
        format: str = "json",
        filters: Optional[Dict] = None,
    ) -> str:
        """Export feature requests to specified format."""
        return await self.repository.export(format, filters)
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _to_model(self, record: Dict) -> FeatureRequest:
        """Convert storage record to Pydantic model."""
        # Handle datetime fields
        created_at = record.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        
        updated_at = record.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        
        return FeatureRequest(
            id=record["id"],
            type=RequestType(record.get("type", "feature_request")),
            title=record.get("title", ""),
            description=record.get("description", ""),
            priority=Priority(record.get("priority", "medium")),
            component=record.get("component"),
            labels=record.get("labels", []),
            steps_to_reproduce=record.get("steps_to_reproduce"),
            expected_behavior=record.get("expected_behavior"),
            actual_behavior=record.get("actual_behavior"),
            environment=record.get("environment"),
            browser=record.get("browser"),
            use_case=record.get("use_case"),
            business_value=record.get("business_value"),
            acceptance_criteria=record.get("acceptance_criteria"),
            status=RequestStatus(record.get("status", "submitted")),
            submitter_id=record.get("submitter_id", ""),
            submitter_email=record.get("submitter_email", ""),
            submitter_name=record.get("submitter_name", ""),
            jira_key=record.get("jira_key"),
            jira_url=record.get("jira_url"),
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
            attachments=record.get("attachments", []),
        )


# =============================================================================
# Module-level convenience functions
# =============================================================================

async def get_service() -> FeatureRequestService:
    """Get the feature request service instance."""
    return await FeatureRequestService.get_instance()


# For backward compatibility
async def create_request(*args, **kwargs):
    service = await get_service()
    return await service.create_request(*args, **kwargs)


async def get_request(request_id: str):
    service = await get_service()
    return await service.get_request(request_id)


async def update_request(*args, **kwargs):
    service = await get_service()
    return await service.update_request(*args, **kwargs)


async def delete_request(request_id: str, deleted_by: str):
    service = await get_service()
    return await service.delete_request(request_id, deleted_by)


async def list_requests(*args, **kwargs):
    service = await get_service()
    return await service.list_requests(*args, **kwargs)


async def get_stats():
    service = await get_service()
    return await service.get_stats()
