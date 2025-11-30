"""
Tenant Data Models
Core data structures for multi-tenant support
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
import uuid


class TenantStatus(str, Enum):
    """Tenant status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class TenantPlan(str, Enum):
    """Tenant subscription plans"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantLimits(BaseModel):
    """Resource limits for a tenant"""
    # API limits
    max_requests_per_hour: int = 100
    max_requests_per_day: int = 1000
    
    # LLM limits
    max_llm_tokens_per_day: int = 100_000
    max_llm_cost_per_month: float = 50.0
    
    # Storage limits
    max_memory_documents: int = 1000
    max_report_storage_mb: int = 100
    
    # Feature limits
    max_agents: int = 5
    max_users: int = 10
    max_projects: int = 5
    
    # Rate limits
    hygiene_checks_per_day: int = 5
    reports_per_day: int = 10
    
    @classmethod
    def for_plan(cls, plan: TenantPlan) -> "TenantLimits":
        """Get limits for a specific plan"""
        limits = {
            TenantPlan.FREE: cls(
                max_requests_per_hour=50,
                max_requests_per_day=500,
                max_llm_tokens_per_day=50_000,
                max_llm_cost_per_month=10.0,
                max_memory_documents=100,
                max_agents=3,
                max_users=3,
                max_projects=2,
            ),
            TenantPlan.STARTER: cls(
                max_requests_per_hour=200,
                max_requests_per_day=2000,
                max_llm_tokens_per_day=200_000,
                max_llm_cost_per_month=50.0,
                max_memory_documents=500,
                max_agents=5,
                max_users=10,
                max_projects=5,
            ),
            TenantPlan.PROFESSIONAL: cls(
                max_requests_per_hour=1000,
                max_requests_per_day=10000,
                max_llm_tokens_per_day=1_000_000,
                max_llm_cost_per_month=200.0,
                max_memory_documents=5000,
                max_agents=10,
                max_users=50,
                max_projects=20,
            ),
            TenantPlan.ENTERPRISE: cls(
                max_requests_per_hour=10000,
                max_requests_per_day=100000,
                max_llm_tokens_per_day=10_000_000,
                max_llm_cost_per_month=1000.0,
                max_memory_documents=50000,
                max_agents=50,
                max_users=500,
                max_projects=100,
            ),
        }
        return limits.get(plan, cls())


class TenantConfig(BaseModel):
    """Tenant-specific configuration"""
    # Jira settings
    jira_url: Optional[str] = None
    jira_username: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_projects: List[str] = Field(default_factory=list)
    
    # GitHub settings
    github_token: Optional[str] = None
    github_org: Optional[str] = None
    github_repos: List[str] = Field(default_factory=list)
    
    # Jenkins settings
    jenkins_url: Optional[str] = None
    jenkins_username: Optional[str] = None
    jenkins_api_token: Optional[str] = None
    
    # Confluence settings
    confluence_url: Optional[str] = None
    confluence_username: Optional[str] = None
    confluence_api_token: Optional[str] = None
    confluence_space_key: Optional[str] = None
    
    # Slack settings
    slack_workspace_id: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_channels: List[str] = Field(default_factory=list)
    
    # LLM settings
    llm_provider: str = "google"
    llm_model: str = "gemini-2.0-flash"
    llm_api_key: Optional[str] = None  # Optional per-tenant key
    
    # Hygiene settings
    hygiene_enabled: bool = True
    hygiene_schedule_hour: int = 9
    hygiene_schedule_days: str = "mon-fri"
    hygiene_required_fields: List[str] = Field(
        default=["labels", "fixVersions", "customfield_10016"]
    )
    
    # Feature flags
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "react_engine": True,
        "vector_memory": True,
        "hygiene_agent": True,
        "slack_integration": True,
        "confluence_reports": True,
        "ai_recommendations": False,
    })


class Tenant(BaseModel):
    """Tenant model representing an organization"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str  # URL-friendly identifier
    
    # Status
    status: TenantStatus = TenantStatus.ACTIVE
    plan: TenantPlan = TenantPlan.FREE
    
    # Ownership
    owner_email: str
    owner_name: Optional[str] = None
    
    # Limits and config
    limits: TenantLimits = Field(default_factory=TenantLimits)
    config: TenantConfig = Field(default_factory=TenantConfig)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Custom metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is URL-friendly"""
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v
    
    def is_active(self) -> bool:
        """Check if tenant is active"""
        return self.status == TenantStatus.ACTIVE
    
    def has_feature(self, feature: str) -> bool:
        """Check if tenant has a feature enabled"""
        return self.config.features.get(feature, False)
    
    def can_use_llm(self, tokens: int) -> bool:
        """Check if tenant can use LLM tokens"""
        # This would typically check against usage tracking
        return True
    
    def to_context(self) -> Dict[str, Any]:
        """Convert to context dict for request handling"""
        return {
            "tenant_id": self.id,
            "tenant_name": self.name,
            "tenant_slug": self.slug,
            "plan": self.plan.value,
            "features": self.config.features,
        }

