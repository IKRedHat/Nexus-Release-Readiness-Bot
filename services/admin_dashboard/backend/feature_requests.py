"""
Feature Request and Bug Report Service

Handles:
- Feature request and bug report submissions
- Automatic Jira ticket creation
- Field mapping between form and Jira
- Request tracking and management
"""

import os
import secrets
from datetime import datetime
from typing import Dict, List, Optional

from nexus_lib.schemas.rbac import (
    FeatureRequest, FeatureRequestCreate, FeatureRequestUpdate,
    RequestType, Priority, RequestStatus,
    JiraFieldMapping,
)
from nexus_lib.utils import AgentClient


# =============================================================================
# CONFIGURATION
# =============================================================================

class FeatureRequestConfig:
    """Feature request configuration"""
    
    # Jira settings
    JIRA_PROJECT_KEY = os.getenv("NEXUS_JIRA_PROJECT", "NEXUS")
    JIRA_AGENT_URL = os.getenv("JIRA_AGENT_URL", "http://localhost:8081")
    
    # Auto-create Jira tickets
    AUTO_CREATE_JIRA = os.getenv("NEXUS_AUTO_CREATE_JIRA", "true").lower() == "true"
    
    # Default field mapping
    DEFAULT_MAPPING = JiraFieldMapping(
        project_key=JIRA_PROJECT_KEY,
        issue_type_feature="Story",
        issue_type_bug="Bug",
    )


# =============================================================================
# IN-MEMORY STORAGE (Replace with database in production)
# =============================================================================

class FeatureRequestStore:
    """In-memory feature request store"""
    
    def __init__(self):
        self.requests: Dict[str, FeatureRequest] = {}
        self.field_mapping: JiraFieldMapping = FeatureRequestConfig.DEFAULT_MAPPING


feature_store = FeatureRequestStore()


# =============================================================================
# JIRA INTEGRATION
# =============================================================================

class JiraIntegration:
    """Handles Jira ticket creation from feature requests"""
    
    @staticmethod
    def map_to_jira_fields(request: FeatureRequest, mapping: JiraFieldMapping) -> Dict:
        """Map feature request fields to Jira API payload"""
        
        # Determine issue type
        issue_type = mapping.issue_type_bug if request.type == RequestType.BUG_REPORT else mapping.issue_type_feature
        
        # Map priority
        jira_priority = mapping.priority_mapping.get(request.priority, "Medium")
        
        # Build description
        description = f"*Submitted by:* {request.submitter_name} ({request.submitter_email})\n\n"
        description += f"*Type:* {request.type.replace('_', ' ').title()}\n\n"
        description += f"---\n\n"
        description += f"h2. Description\n{request.description}\n\n"
        
        if request.type == RequestType.BUG_REPORT:
            if request.steps_to_reproduce:
                description += f"h2. Steps to Reproduce\n{request.steps_to_reproduce}\n\n"
            if request.expected_behavior:
                description += f"h2. Expected Behavior\n{request.expected_behavior}\n\n"
            if request.actual_behavior:
                description += f"h2. Actual Behavior\n{request.actual_behavior}\n\n"
            if request.environment:
                description += f"h2. Environment\n{request.environment}\n\n"
            if request.browser:
                description += f"h2. Browser\n{request.browser}\n\n"
        else:
            if request.use_case:
                description += f"h2. Use Case\n{request.use_case}\n\n"
            if request.business_value:
                description += f"h2. Business Value\n{request.business_value}\n\n"
            if request.acceptance_criteria:
                description += f"h2. Acceptance Criteria\n{request.acceptance_criteria}\n\n"
        
        # Build labels
        labels = [f"{mapping.label_prefix}{l}" for l in request.labels]
        labels.append(f"{mapping.label_prefix}submitted-via-dashboard")
        labels.append(f"{mapping.label_prefix}{request.type}")
        
        # Build Jira payload
        jira_payload = {
            "fields": {
                "project": {"key": mapping.project_key},
                "summary": request.title,
                "description": description,
                "issuetype": {"name": issue_type},
                "priority": {"name": jira_priority},
                "labels": labels,
            }
        }
        
        # Add component if specified
        if request.component:
            jira_payload["fields"]["components"] = [{"name": request.component}]
        
        # Add environment for bugs
        if request.type == RequestType.BUG_REPORT and request.environment:
            jira_payload["fields"]["environment"] = request.environment
        
        return jira_payload
    
    @staticmethod
    async def create_jira_ticket(request: FeatureRequest) -> Optional[Dict]:
        """Create a Jira ticket via the Jira Agent"""
        if not FeatureRequestConfig.AUTO_CREATE_JIRA:
            return None
        
        try:
            # Map fields
            jira_payload = JiraIntegration.map_to_jira_fields(
                request, 
                feature_store.field_mapping
            )
            
            # Call Jira Agent
            client = AgentClient(FeatureRequestConfig.JIRA_AGENT_URL)
            response = await client.post(
                "/execute",
                json={
                    "action": "create_issue",
                    "payload": jira_payload,
                },
            )
            
            if response and response.get("success"):
                return {
                    "key": response.get("data", {}).get("key"),
                    "url": response.get("data", {}).get("self"),
                }
            
            return None
            
        except Exception as e:
            print(f"Failed to create Jira ticket: {e}")
            return None


# =============================================================================
# FEATURE REQUEST SERVICE
# =============================================================================

class FeatureRequestService:
    """Service for managing feature requests and bug reports"""
    
    @staticmethod
    async def create_request(
        data: FeatureRequestCreate,
        submitter_id: str,
        submitter_email: str,
        submitter_name: str,
    ) -> FeatureRequest:
        """Create a new feature request or bug report"""
        
        request_id = f"fr-{secrets.token_hex(8)}"
        
        request = FeatureRequest(
            id=request_id,
            type=data.type,
            title=data.title,
            description=data.description,
            priority=data.priority,
            component=data.component,
            labels=data.labels,
            steps_to_reproduce=data.steps_to_reproduce,
            expected_behavior=data.expected_behavior,
            actual_behavior=data.actual_behavior,
            environment=data.environment,
            browser=data.browser,
            use_case=data.use_case,
            business_value=data.business_value,
            acceptance_criteria=data.acceptance_criteria,
            submitter_id=submitter_id,
            submitter_email=submitter_email,
            submitter_name=submitter_name,
        )
        
        # Create Jira ticket
        jira_result = await JiraIntegration.create_jira_ticket(request)
        if jira_result:
            request.jira_key = jira_result.get("key")
            request.jira_url = jira_result.get("url")
            request.status = RequestStatus.TRIAGED
        
        # Store request
        feature_store.requests[request_id] = request
        
        return request
    
    @staticmethod
    def get_request(request_id: str) -> Optional[FeatureRequest]:
        """Get a feature request by ID"""
        return feature_store.requests.get(request_id)
    
    @staticmethod
    def update_request(request_id: str, data: FeatureRequestUpdate) -> Optional[FeatureRequest]:
        """Update a feature request"""
        request = feature_store.requests.get(request_id)
        if not request:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(request, key, value)
        
        request.updated_at = datetime.utcnow()
        feature_store.requests[request_id] = request
        
        return request
    
    @staticmethod
    def delete_request(request_id: str) -> bool:
        """Delete a feature request"""
        if request_id in feature_store.requests:
            del feature_store.requests[request_id]
            return True
        return False
    
    @staticmethod
    def list_requests(
        type_filter: Optional[RequestType] = None,
        status_filter: Optional[RequestStatus] = None,
        submitter_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[FeatureRequest]:
        """List feature requests with optional filters"""
        requests = list(feature_store.requests.values())
        
        if type_filter:
            requests = [r for r in requests if r.type == type_filter]
        
        if status_filter:
            requests = [r for r in requests if r.status == status_filter]
        
        if submitter_id:
            requests = [r for r in requests if r.submitter_id == submitter_id]
        
        # Sort by created_at descending
        requests.sort(key=lambda x: x.created_at, reverse=True)
        
        return requests[:limit]
    
    @staticmethod
    def get_stats() -> Dict:
        """Get feature request statistics"""
        requests = list(feature_store.requests.values())
        
        return {
            "total": len(requests),
            "by_type": {
                "feature_request": len([r for r in requests if r.type == RequestType.FEATURE_REQUEST]),
                "bug_report": len([r for r in requests if r.type == RequestType.BUG_REPORT]),
                "improvement": len([r for r in requests if r.type == RequestType.IMPROVEMENT]),
                "documentation": len([r for r in requests if r.type == RequestType.DOCUMENTATION]),
                "question": len([r for r in requests if r.type == RequestType.QUESTION]),
            },
            "by_status": {
                "submitted": len([r for r in requests if r.status == RequestStatus.SUBMITTED]),
                "triaged": len([r for r in requests if r.status == RequestStatus.TRIAGED]),
                "in_progress": len([r for r in requests if r.status == RequestStatus.IN_PROGRESS]),
                "completed": len([r for r in requests if r.status == RequestStatus.COMPLETED]),
                "rejected": len([r for r in requests if r.status == RequestStatus.REJECTED]),
            },
            "by_priority": {
                "critical": len([r for r in requests if r.priority == Priority.CRITICAL]),
                "high": len([r for r in requests if r.priority == Priority.HIGH]),
                "medium": len([r for r in requests if r.priority == Priority.MEDIUM]),
                "low": len([r for r in requests if r.priority == Priority.LOW]),
            },
            "with_jira": len([r for r in requests if r.jira_key]),
        }
    
    # -------------------------------------------------------------------------
    # Field Mapping Management
    # -------------------------------------------------------------------------
    
    @staticmethod
    def get_field_mapping() -> JiraFieldMapping:
        """Get current Jira field mapping"""
        return feature_store.field_mapping
    
    @staticmethod
    def update_field_mapping(mapping: JiraFieldMapping) -> JiraFieldMapping:
        """Update Jira field mapping"""
        feature_store.field_mapping = mapping
        return mapping
    
    # -------------------------------------------------------------------------
    # Component Management
    # -------------------------------------------------------------------------
    
    @staticmethod
    def get_available_components() -> List[str]:
        """Get list of available components for selection"""
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
        """Get list of available labels for selection"""
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

