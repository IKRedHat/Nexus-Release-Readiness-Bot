"""
RBAC (Role-Based Access Control) Schemas for Nexus Admin Dashboard

This module defines the data models for:
- Users with SSO integration
- Dynamic roles with granular permissions
- Role-user assignments
- Feature requests and bug reports
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, EmailStr


# =============================================================================
# PERMISSION DEFINITIONS
# =============================================================================

class Permission(str, Enum):
    """Granular permissions for RBAC system"""
    
    # Dashboard permissions
    VIEW_DASHBOARD = "dashboard:view"
    VIEW_METRICS = "dashboard:metrics:view"
    VIEW_RELEASES = "dashboard:releases:view"
    
    # Configuration permissions
    VIEW_CONFIG = "config:view"
    EDIT_CONFIG = "config:edit"
    EDIT_CREDENTIALS = "config:credentials:edit"
    TOGGLE_MODE = "config:mode:toggle"
    
    # Agent permissions
    VIEW_AGENTS = "agents:view"
    RESTART_AGENTS = "agents:restart"
    CONFIGURE_AGENTS = "agents:configure"
    
    # Release management
    VIEW_RELEASES_DETAIL = "releases:view"
    CREATE_RELEASE = "releases:create"
    EDIT_RELEASE = "releases:edit"
    DELETE_RELEASE = "releases:delete"
    IMPORT_RELEASES = "releases:import"
    
    # User management (Admin only)
    VIEW_USERS = "users:view"
    CREATE_USER = "users:create"
    EDIT_USER = "users:edit"
    DELETE_USER = "users:delete"
    ASSIGN_ROLES = "users:roles:assign"
    
    # Role management (Admin only)
    VIEW_ROLES = "roles:view"
    CREATE_ROLE = "roles:create"
    EDIT_ROLE = "roles:edit"
    DELETE_ROLE = "roles:delete"
    
    # Feature requests
    SUBMIT_FEATURE_REQUEST = "features:submit"
    VIEW_FEATURE_REQUESTS = "features:view"
    MANAGE_FEATURE_REQUESTS = "features:manage"
    
    # Observability
    VIEW_OBSERVABILITY = "observability:view"
    CONFIGURE_ALERTS = "observability:alerts:configure"
    
    # API access
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"
    
    # System administration
    SYSTEM_ADMIN = "system:admin"
    AUDIT_LOGS = "system:audit:view"


# =============================================================================
# PREDEFINED ROLE TEMPLATES
# =============================================================================

ROLE_TEMPLATES: Dict[str, Set[str]] = {
    "admin": {
        Permission.SYSTEM_ADMIN,
        Permission.VIEW_DASHBOARD, Permission.VIEW_METRICS, Permission.VIEW_RELEASES,
        Permission.VIEW_CONFIG, Permission.EDIT_CONFIG, Permission.EDIT_CREDENTIALS, Permission.TOGGLE_MODE,
        Permission.VIEW_AGENTS, Permission.RESTART_AGENTS, Permission.CONFIGURE_AGENTS,
        Permission.VIEW_RELEASES_DETAIL, Permission.CREATE_RELEASE, Permission.EDIT_RELEASE, 
        Permission.DELETE_RELEASE, Permission.IMPORT_RELEASES,
        Permission.VIEW_USERS, Permission.CREATE_USER, Permission.EDIT_USER, 
        Permission.DELETE_USER, Permission.ASSIGN_ROLES,
        Permission.VIEW_ROLES, Permission.CREATE_ROLE, Permission.EDIT_ROLE, Permission.DELETE_ROLE,
        Permission.SUBMIT_FEATURE_REQUEST, Permission.VIEW_FEATURE_REQUESTS, Permission.MANAGE_FEATURE_REQUESTS,
        Permission.VIEW_OBSERVABILITY, Permission.CONFIGURE_ALERTS,
        Permission.API_READ, Permission.API_WRITE, Permission.API_ADMIN,
        Permission.AUDIT_LOGS,
    },
    "developer": {
        Permission.VIEW_DASHBOARD, Permission.VIEW_METRICS, Permission.VIEW_RELEASES,
        Permission.VIEW_CONFIG,
        Permission.VIEW_AGENTS,
        Permission.VIEW_RELEASES_DETAIL,
        Permission.SUBMIT_FEATURE_REQUEST, Permission.VIEW_FEATURE_REQUESTS,
        Permission.VIEW_OBSERVABILITY,
        Permission.API_READ,
    },
    "engineering_manager": {
        Permission.VIEW_DASHBOARD, Permission.VIEW_METRICS, Permission.VIEW_RELEASES,
        Permission.VIEW_CONFIG, Permission.EDIT_CONFIG, Permission.TOGGLE_MODE,
        Permission.VIEW_AGENTS, Permission.RESTART_AGENTS,
        Permission.VIEW_RELEASES_DETAIL, Permission.CREATE_RELEASE, Permission.EDIT_RELEASE,
        Permission.VIEW_USERS,
        Permission.SUBMIT_FEATURE_REQUEST, Permission.VIEW_FEATURE_REQUESTS,
        Permission.VIEW_OBSERVABILITY, Permission.CONFIGURE_ALERTS,
        Permission.API_READ, Permission.API_WRITE,
    },
    "senior_management": {
        Permission.VIEW_DASHBOARD, Permission.VIEW_METRICS, Permission.VIEW_RELEASES,
        Permission.VIEW_CONFIG,
        Permission.VIEW_AGENTS,
        Permission.VIEW_RELEASES_DETAIL,
        Permission.VIEW_USERS,
        Permission.SUBMIT_FEATURE_REQUEST, Permission.VIEW_FEATURE_REQUESTS,
        Permission.VIEW_OBSERVABILITY,
        Permission.AUDIT_LOGS,
    },
    "executive_management": {
        Permission.VIEW_DASHBOARD, Permission.VIEW_METRICS, Permission.VIEW_RELEASES,
        Permission.VIEW_RELEASES_DETAIL,
        Permission.VIEW_FEATURE_REQUESTS,
        Permission.VIEW_OBSERVABILITY,
        Permission.AUDIT_LOGS,
    },
    "product_manager": {
        Permission.VIEW_DASHBOARD, Permission.VIEW_METRICS, Permission.VIEW_RELEASES,
        Permission.VIEW_CONFIG,
        Permission.VIEW_AGENTS,
        Permission.VIEW_RELEASES_DETAIL, Permission.CREATE_RELEASE, Permission.EDIT_RELEASE, Permission.IMPORT_RELEASES,
        Permission.SUBMIT_FEATURE_REQUEST, Permission.VIEW_FEATURE_REQUESTS, Permission.MANAGE_FEATURE_REQUESTS,
        Permission.VIEW_OBSERVABILITY,
        Permission.API_READ,
    },
    "project_manager": {
        Permission.VIEW_DASHBOARD, Permission.VIEW_METRICS, Permission.VIEW_RELEASES,
        Permission.VIEW_CONFIG,
        Permission.VIEW_AGENTS,
        Permission.VIEW_RELEASES_DETAIL, Permission.EDIT_RELEASE,
        Permission.SUBMIT_FEATURE_REQUEST, Permission.VIEW_FEATURE_REQUESTS,
        Permission.VIEW_OBSERVABILITY,
    },
    "qa_engineer": {
        Permission.VIEW_DASHBOARD, Permission.VIEW_METRICS, Permission.VIEW_RELEASES,
        Permission.VIEW_CONFIG,
        Permission.VIEW_AGENTS,
        Permission.VIEW_RELEASES_DETAIL,
        Permission.SUBMIT_FEATURE_REQUEST, Permission.VIEW_FEATURE_REQUESTS,
        Permission.VIEW_OBSERVABILITY,
        Permission.API_READ,
    },
    "viewer": {
        Permission.VIEW_DASHBOARD, Permission.VIEW_METRICS, Permission.VIEW_RELEASES,
        Permission.VIEW_RELEASES_DETAIL,
        Permission.VIEW_OBSERVABILITY,
    },
}


# =============================================================================
# USER MODELS
# =============================================================================

class SSOProvider(str, Enum):
    """Supported SSO providers"""
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    GOOGLE = "google"
    GITHUB = "github"
    SAML = "saml"
    LOCAL = "local"  # For development/testing


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class User(BaseModel):
    """User model with SSO integration"""
    id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., description="Full name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    
    # SSO fields
    sso_provider: SSOProvider = Field(default=SSOProvider.LOCAL)
    sso_id: Optional[str] = Field(None, description="External SSO identifier")
    
    # Role assignments
    roles: List[str] = Field(default_factory=list, description="Assigned role IDs")
    
    # Status and metadata
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Additional attributes
    department: Optional[str] = None
    title: Optional[str] = None
    manager_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class UserCreate(BaseModel):
    """Model for creating a new user"""
    email: EmailStr
    name: str
    roles: List[str] = Field(default_factory=list)
    department: Optional[str] = None
    title: Optional[str] = None
    sso_provider: SSOProvider = SSOProvider.LOCAL


class UserUpdate(BaseModel):
    """Model for updating a user"""
    name: Optional[str] = None
    roles: Optional[List[str]] = None
    status: Optional[UserStatus] = None
    department: Optional[str] = None
    title: Optional[str] = None


class UserWithPermissions(User):
    """User model with computed permissions"""
    permissions: Set[str] = Field(default_factory=set)
    is_admin: bool = False


# =============================================================================
# ROLE MODELS
# =============================================================================

class Role(BaseModel):
    """Dynamic role with permissions"""
    id: str = Field(..., description="Unique role identifier")
    name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Role description")
    
    # Permissions
    permissions: Set[str] = Field(default_factory=set)
    
    # Metadata
    is_system_role: bool = Field(default=False, description="Cannot be deleted if True")
    is_default: bool = Field(default=False, description="Auto-assign to new users")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    # Hierarchy
    parent_role_id: Optional[str] = Field(None, description="Inherits permissions from parent")
    
    class Config:
        use_enum_values = True


class RoleCreate(BaseModel):
    """Model for creating a new role"""
    name: str
    description: Optional[str] = None
    permissions: Set[str] = Field(default_factory=set)
    parent_role_id: Optional[str] = None
    is_default: bool = False


class RoleUpdate(BaseModel):
    """Model for updating a role"""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Set[str]] = None
    parent_role_id: Optional[str] = None
    is_default: Optional[bool] = None


# =============================================================================
# FEATURE REQUEST / BUG REPORT MODELS
# =============================================================================

class RequestType(str, Enum):
    """Type of submission"""
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    IMPROVEMENT = "improvement"
    DOCUMENTATION = "documentation"
    QUESTION = "question"


class Priority(str, Enum):
    """Priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RequestStatus(str, Enum):
    """Status of the request"""
    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class FeatureRequest(BaseModel):
    """Feature request or bug report model"""
    id: str = Field(..., description="Unique request identifier")
    
    # Core fields
    type: RequestType
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=5000)
    
    # Classification
    priority: Priority = Priority.MEDIUM
    component: Optional[str] = Field(None, description="Affected component/service")
    labels: List[str] = Field(default_factory=list)
    
    # Bug-specific fields
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    environment: Optional[str] = None  # e.g., "Production", "Staging"
    browser: Optional[str] = None
    
    # Feature-specific fields
    use_case: Optional[str] = None
    business_value: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    
    # Metadata
    status: RequestStatus = RequestStatus.SUBMITTED
    submitter_id: str
    submitter_email: EmailStr
    submitter_name: str
    
    # Jira integration
    jira_key: Optional[str] = Field(None, description="Created Jira ticket key")
    jira_url: Optional[str] = Field(None, description="Link to Jira ticket")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Attachments
    attachments: List[str] = Field(default_factory=list, description="URLs to attachments")
    
    class Config:
        use_enum_values = True


class FeatureRequestCreate(BaseModel):
    """Model for submitting a feature request or bug report"""
    type: RequestType
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=5000)
    priority: Priority = Priority.MEDIUM
    component: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    
    # Bug-specific
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    environment: Optional[str] = None
    browser: Optional[str] = None
    
    # Feature-specific
    use_case: Optional[str] = None
    business_value: Optional[str] = None
    acceptance_criteria: Optional[str] = None


class FeatureRequestUpdate(BaseModel):
    """Model for updating a feature request"""
    status: Optional[RequestStatus] = None
    priority: Optional[Priority] = None
    labels: Optional[List[str]] = None
    jira_key: Optional[str] = None
    jira_url: Optional[str] = None


# =============================================================================
# JIRA FIELD MAPPING
# =============================================================================

class JiraFieldMapping(BaseModel):
    """Mapping of feature request fields to Jira fields"""
    
    # Standard Jira fields
    project_key: str = Field(..., description="Jira project key")
    issue_type_feature: str = Field(default="Story", description="Issue type for features")
    issue_type_bug: str = Field(default="Bug", description="Issue type for bugs")
    
    # Priority mapping
    priority_mapping: Dict[str, str] = Field(
        default={
            "critical": "Highest",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
        }
    )
    
    # Custom field mappings (Jira custom field IDs)
    custom_fields: Dict[str, str] = Field(
        default={
            "component": "components",  # Standard field
            "environment": "environment",  # Standard field
            "business_value": "customfield_10100",  # Example custom field
            "acceptance_criteria": "customfield_10101",
        }
    )
    
    # Label prefix for auto-generated labels
    label_prefix: str = Field(default="nexus-")


# =============================================================================
# AUTHENTICATION MODELS
# =============================================================================

class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # User ID
    email: EmailStr
    name: str
    roles: List[str]
    permissions: List[str]
    exp: datetime
    iat: datetime
    iss: str = "nexus-admin"


class AuthToken(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    refresh_token: Optional[str] = None
    user: UserWithPermissions


class SSOConfig(BaseModel):
    """SSO provider configuration"""
    provider: SSOProvider
    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str
    userinfo_url: str
    scopes: List[str] = Field(default=["openid", "email", "profile"])
    redirect_uri: str
    
    # Optional SAML-specific
    idp_metadata_url: Optional[str] = None
    sp_entity_id: Optional[str] = None


# =============================================================================
# AUDIT LOG MODELS
# =============================================================================

class AuditAction(str, Enum):
    """Types of auditable actions"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ROLE_ASSIGN = "role_assign"
    ROLE_REVOKE = "role_revoke"
    CONFIG_CHANGE = "config_change"
    FEATURE_SUBMIT = "feature_submit"


class AuditLog(BaseModel):
    """Audit log entry"""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    user_email: EmailStr
    action: AuditAction
    resource_type: str  # e.g., "user", "role", "config"
    resource_id: Optional[str] = None
    details: Dict = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        use_enum_values = True


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class RBACStats(BaseModel):
    """Statistics for RBAC dashboard"""
    total_users: int
    active_users: int
    total_roles: int
    feature_requests_pending: int
    feature_requests_completed: int


class PermissionCheck(BaseModel):
    """Result of a permission check"""
    user_id: str
    permission: str
    allowed: bool
    roles_granting: List[str] = Field(default_factory=list)

